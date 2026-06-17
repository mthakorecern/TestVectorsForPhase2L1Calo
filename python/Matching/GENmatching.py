#!/usr/bin/env python3

import argparse
import csv
import math
from array import array
from pathlib import Path
import ROOT

## We define some constants that are necessary for conversion of the local eta-phi co-ordinate to global eta-phi coordinate

## Based on https://github.com/rpsimeon34/cmssw/blob/from-CMSSW_15_0_0_pre3/L1Trigger/L1CaloTrigger/interface/RCT_IO.h

ECAL_ETA_RANGE = 1.4841

N_TOWERS_ETA = 17
N_TOWERS_PHI = 6
N_CARDS = 24

CRYSTALS_IN_TOWER_ETA = 5
CRYSTALS_IN_TOWER_PHI = 5

N_CRYSTAL_ETA_HALF = N_TOWERS_ETA * CRYSTALS_IN_TOWER_ETA       # 85
N_CRYSTAL_ETA_FULL = 2 * N_CRYSTAL_ETA_HALF  # 170
N_CRYSTAL_PHI_CARD = N_TOWERS_PHI * CRYSTALS_IN_TOWER_PHI       # 30
N_CRYSTAL_PHI_FULL = N_CRYSTAL_PHI_CARD * (N_CARDS // 2)        # 360

DEFAULT_MATCH_DR = 0.2


def to_float(x, default=0.0):
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default


def to_int(x, default=0):
    try:
        if x is None or x == "":
            return default
        return int(float(x))
    except Exception:
        return default


def read_csv_dicts(path):
    rows = []

    if not path.exists():
        return rows

    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def normalize_phi(phi):
    while phi >= math.pi:
        phi -= 2.0 * math.pi
    while phi < -math.pi:
        phi += 2.0 * math.pi
    return phi


def delta_phi(phi1, phi2):
    return normalize_phi(phi1 - phi2)

def delta_r(eta1, phi1, eta2, phi2):
    d_eta = eta1 - eta2
    d_phi = delta_phi(phi1, phi2)
    return math.sqrt(d_eta * d_eta + d_phi * d_phi)

def get_card_ref_crystal_ieta(card):
    """
    Exact Python equivalent of
    p2rctIO::getCard_refCrystal_iEta(card).
    """
    if card < 0 or card >= N_CARDS:
        return -999

    if card % 2 == 1:
        # Odd card: positive eta
        return N_CRYSTAL_ETA_HALF
    else:
        # Even card: negative eta
        return N_CRYSTAL_ETA_HALF - 1

def get_card_ref_crystal_iphi(card):
    """
    Exact Python equivalent of
    p2rctIO::getCard_refCrystal_iPhi(card).
    """
    if card < 0 or card >= N_CARDS:
        return -999

    if card % 2 == 1:
        # Odd card: positive eta
        return (
            (card // 2) * N_CRYSTAL_PHI_CARD
        )
    else:
        # Even card: negative eta
        return (
            ((card // 2) + 1) * N_CRYSTAL_PHI_CARD
            - 1
        )

def ip3_rct_eta_to_local_ieta(rct_eta):
    """
    Undo IP21 encoding:

        rctEta = etaInSLR + 25 * slr
    """

    if rct_eta < 0 or rct_eta >= 100:
        return -999

    slr = rct_eta // 25
    eta_in_slr = rct_eta % 25

    # SLR0 is only 2 towers = 10 crystals.
    if slr == 0 and eta_in_slr >= 10:
        return -999

    local_ieta = (
        (3 - slr) * 25
        + eta_in_slr
    )

    if not (
        0 <= local_ieta < N_CRYSTAL_ETA_HALF
    ):
        return -999

    return local_ieta

def ip3_rct_phi_to_local_iphi(rct_phi):
    if not (
        0 <= rct_phi < N_CRYSTAL_PHI_CARD
    ):
        return -999

    return rct_phi


def card_local_to_global_crystal(
    card,
    local_ieta,
    local_iphi,
):
    """
    Invert:

      local_iEta =
          abs(ref_global_iEta - global_iEta)

      local_iPhi =
          abs(ref_global_iPhi - global_iPhi)

    following RCT_IO.h exactly.
    """

    if card < 0 or card >= N_CARDS:
        return -999, -999

    if (
        local_ieta < 0
        or local_ieta >= N_CRYSTAL_ETA_HALF
    ):
        return -999, -999

    if (
        local_iphi < 0
        or local_iphi >= N_CRYSTAL_PHI_CARD
    ):
        return -999, -999

    ref_ieta = get_card_ref_crystal_ieta(card)
    ref_iphi = get_card_ref_crystal_iphi(card)

    if card % 2 == 1:
        # Positive eta:
        # indices increase away from the reference crystal.
        global_ieta = ref_ieta + local_ieta
        global_iphi = ref_iphi + local_iphi

    else:
        # Negative eta:
        # indices decrease away from the reference crystal.
        global_ieta = ref_ieta - local_ieta
        global_iphi = ref_iphi - local_iphi

    # Phi is periodic.
    global_iphi %= N_CRYSTAL_PHI_FULL

    if not (
        0 <= global_ieta < N_CRYSTAL_ETA_FULL
    ):
        return -999, -999

    return global_ieta, global_iphi


def global_crystal_to_physical_eta_phi(global_ieta, global_iphi):
    """
    Invert SimpleCaloHit::crystaliEta() and crystaliPhi()
    using the center of the indexed crystal bin.
    """

    if not (
        0 <= global_ieta < N_CRYSTAL_ETA_FULL
    ):
        return -999.0, -999.0

    if not (
        0 <= global_iphi < N_CRYSTAL_PHI_FULL
    ):
        return -999.0, -999.0

    eta_cell = (
        ECAL_ETA_RANGE
        / float(N_CRYSTAL_ETA_HALF)
    )

    phi_cell = (
        2.0 * math.pi
        / float(N_CRYSTAL_PHI_FULL)
    )

    eta = (
        (global_ieta + 0.5) * eta_cell
        - ECAL_ETA_RANGE
    )

    phi = (
        (global_iphi + 0.5) * phi_cell
        - math.pi
    )

    return eta, normalize_phi(phi)


def card_local_to_physical_eta_phi(card, local_ieta, local_iphi):
    global_ieta, global_iphi = card_local_to_global_crystal(
        card,
        local_ieta,
        local_iphi,
    )

    eta, phi = global_crystal_to_physical_eta_phi(
        global_ieta,
        global_iphi,
    )

    return eta, phi, global_ieta, global_iphi


def ip3_cluster_hw_to_physical_eta_phi(card, rct_eta_hw, rct_phi_hw):
    local_ieta = ip3_rct_eta_to_local_ieta(rct_eta_hw)
    local_iphi = ip3_rct_phi_to_local_iphi(rct_phi_hw)

    if local_ieta < 0 or local_iphi < 0:
        return {
            "local_ieta": -999,
            "local_iphi": -999,
            "global_ieta": -999,
            "global_iphi": -999,
            "eta": -999.0,
            "phi": -999.0,
        }

    eta, phi, global_ieta, global_iphi = (
        card_local_to_physical_eta_phi(
            card,
            local_ieta,
            local_iphi,
        )
    )

    return {
        "local_ieta": local_ieta,
        "local_iphi": local_iphi,
        "global_ieta": global_ieta,
        "global_iphi": global_iphi,
        "eta": eta,
        "phi": phi,
    }



def read_ip3_rct_clusters(event_dir, card, energy_lsb):
    """
    Read final IP3 RCT clusters from:

        event_<event>/card_<card>/decoded/IP3/card_<card>_IP3_output_decoded.csv

    Expected header:
        card,event,link_index,object_type,index,raw_hex,
        seedEnergy,clusterEnergy,eta,phi,et5x5,wps,...

    Keep:
        object_type == rct_cluster
        clusterEnergy > 0
    """

    ip3_path = (
        event_dir
        / f"card_{card}"
        / "decoded"
        / "IP3"
        / f"card_{card}_IP3_output_decoded.csv"
    )

    rows = read_csv_dicts(ip3_path)
    clusters = []

    for row in rows:
        if row.get("object_type") != "rct_cluster":
            continue

        raw_energy = to_float(row.get("clusterEnergy"), 0.0)
        if raw_energy <= 0.0:
            continue

        raw_seed = to_float(row.get("seedEnergy"), 0.0)
        raw_et5x5 = to_float(row.get("et5x5"), 0.0)

        rct_eta_hw = to_int(row.get("eta"), -999)
        rct_phi_hw = to_int(row.get("phi"), -999)

        coord = ip3_cluster_hw_to_physical_eta_phi(
            card,
            rct_eta_hw,
            rct_phi_hw,
        )

        if coord["eta"] < -900 or coord["phi"] < -900:
            continue

        cluster = {
            "card": card,
            "index": to_int(row.get("index"), -1),
            "raw_hex": row.get("raw_hex", ""),

            "raw_energy": raw_energy,
            "raw_seed": raw_seed,
            "raw_et5x5": raw_et5x5,

            "pt": raw_energy * energy_lsb,
            "seed_pt": raw_seed * energy_lsb,
            "et5x5": raw_et5x5 * energy_lsb,
            "et2x5": -999.0,

            "rct_eta_hw": rct_eta_hw,
            "rct_phi_hw": rct_phi_hw,

            "local_ieta": coord["local_ieta"],
            "local_iphi": coord["local_iphi"],
            "global_ieta": coord["global_ieta"],
            "global_iphi": coord["global_iphi"],

            "eta": coord["eta"],
            "phi": coord["phi"],
        }

        clusters.append(cluster)

    # Original analyzer sorts RCT cluster info by pT before matching/selection.
    clusters.sort(key=lambda c: c["pt"], reverse=True)

    return clusters



# ============================================================
# ROOT tree creation
# ============================================================

def make_branch(tree, branches, name, root_type):
    if root_type == "I":
        branches[name] = array("i", [0])
    elif root_type == "D":
        branches[name] = array("d", [0.0])
    else:
        raise RuntimeError(f"Unsupported ROOT branch type: {root_type}")

    tree.Branch(name, branches[name], f"{name}/{root_type}")


def create_output_tree(output_root_path):
    fout = ROOT.TFile(output_root_path, "RECREATE")

    # This matches your plotting code:
    # tree_path = "l1NtupleProducer/efficiencyTree"
    out_dir = fout.mkdir("l1NtupleProducer")
    out_dir.cd()

    tree = ROOT.TTree("efficiencyTree", "Efficiency Tree")

    branches = {}

    # Original analyzer-style scalar branches
    make_branch(tree, branches, "run", "I")
    make_branch(tree, branches, "lumi", "I")
    make_branch(tree, branches, "event", "I")
    make_branch(tree, branches, "nvtx", "I")

    make_branch(tree, branches, "genPt", "D")
    make_branch(tree, branches, "genEta", "D")
    make_branch(tree, branches, "genPhi", "D")

    make_branch(tree, branches, "rct_cPt", "D")
    make_branch(tree, branches, "rct_cEta", "D")
    make_branch(tree, branches, "rct_cPhi", "D")
    make_branch(tree, branches, "rct_deltaR", "D")
    make_branch(tree, branches, "rct_et2x5", "D")
    make_branch(tree, branches, "rct_et5x5", "D")

    # GCT branches included for compatibility with old analyzer format.
    # Filled with defaults.
    make_branch(tree, branches, "gct_cPt", "D")
    make_branch(tree, branches, "gct_cEta", "D")
    make_branch(tree, branches, "gct_cPhi", "D")
    make_branch(tree, branches, "gct_deltaR", "D")
    make_branch(tree, branches, "gct_et2x5", "D")
    make_branch(tree, branches, "gct_et5x5", "D")
    make_branch(tree, branches, "gct_iso", "D")
    make_branch(tree, branches, "gct_is_ss", "I")
    make_branch(tree, branches, "gct_is_looseTkss", "I")
    make_branch(tree, branches, "gct_is_iso", "I")
    make_branch(tree, branches, "gct_is_looseTkiso", "I")

    # Debug branches. Your current plotting code ignores these.
    make_branch(tree, branches, "gen_idx", "I")
    make_branch(tree, branches, "pdgId", "I")
    make_branch(tree, branches, "status", "I")

    make_branch(tree, branches, "gen_rct_card", "I")
    make_branch(tree, branches, "gen_crystal_iEta", "I")
    make_branch(tree, branches, "gen_crystal_iPhi", "I")
    make_branch(tree, branches, "gen_local_iEta", "I")
    make_branch(tree, branches, "gen_local_iPhi", "I")

    make_branch(tree, branches, "rct_matchPass", "I")
    make_branch(tree, branches, "rct_clusterIdx", "I")
    make_branch(tree, branches, "rct_rawEnergy", "D")
    make_branch(tree, branches, "rct_seedEnergy", "D")
    make_branch(tree, branches, "rct_hwEta", "I")
    make_branch(tree, branches, "rct_hwPhi", "I")
    make_branch(tree, branches, "rct_local_iEta", "I")
    make_branch(tree, branches, "rct_local_iPhi", "I")
    make_branch(tree, branches, "rct_global_iEta", "I")
    make_branch(tree, branches, "rct_global_iPhi", "I")
    make_branch(tree, branches, "rct_card", "I")

    return fout, tree, branches


def reset_branches(branches):
    for _, arr in branches.items():
        if arr.typecode == "i":
            arr[0] = 0
        else:
            arr[0] = 0.0

    branches["nvtx"][0] = 0

    # RCT unmatched defaults
    branches["rct_cPt"][0] = 0.0
    branches["rct_cEta"][0] = -999.0
    branches["rct_cPhi"][0] = -999.0
    branches["rct_deltaR"][0] = 999.0
    branches["rct_et2x5"][0] = -999.0
    branches["rct_et5x5"][0] = 0.0

    # GCT defaults
    branches["gct_cPt"][0] = 0.0
    branches["gct_cEta"][0] = -999.0
    branches["gct_cPhi"][0] = -999.0
    branches["gct_deltaR"][0] = 999.0
    branches["gct_et2x5"][0] = 0.0
    branches["gct_et5x5"][0] = 0.0
    branches["gct_iso"][0] = 0.0
    branches["gct_is_ss"][0] = 0
    branches["gct_is_looseTkss"][0] = 0
    branches["gct_is_iso"][0] = 0
    branches["gct_is_looseTkiso"][0] = 0

    # Debug defaults
    branches["gen_idx"][0] = -1
    branches["pdgId"][0] = 0
    branches["status"][0] = 0

    branches["gen_rct_card"][0] = -1
    branches["gen_crystal_iEta"][0] = -999
    branches["gen_crystal_iPhi"][0] = -999
    branches["gen_local_iEta"][0] = -999
    branches["gen_local_iPhi"][0] = -999

    branches["rct_matchPass"][0] = 0
    branches["rct_clusterIdx"][0] = -1
    branches["rct_rawEnergy"][0] = 0.0
    branches["rct_seedEnergy"][0] = 0.0
    branches["rct_hwEta"][0] = -999
    branches["rct_hwPhi"][0] = -999
    branches["rct_local_iEta"][0] = -999
    branches["rct_local_iPhi"][0] = -999
    branches["rct_global_iEta"][0] = -999
    branches["rct_global_iPhi"][0] = -999
    branches["rct_card"][0] = -1


# ============================================================
# Event processing
# ============================================================

def find_gen_csv(event_dir):
    matches = sorted(event_dir.glob("event_*_gen_electrons.csv"))
    if len(matches) == 0:
        return None
    return matches[0]


def fill_gen_branches(branches, gen):
    branches["run"][0] = to_int(gen.get("run"), 0)
    branches["lumi"][0] = to_int(gen.get("lumi"), 0)
    branches["event"][0] = to_int(gen.get("event"), 0)

    branches["gen_idx"][0] = to_int(gen.get("gen_idx"), -1)
    branches["pdgId"][0] = to_int(gen.get("pdgId"), 0)
    branches["status"][0] = to_int(gen.get("status"), 0)

    # Use propagated ECAL eta/phi exactly like the original analyzer matching.
    branches["genPt"][0] = to_float(
        gen.get("gen_ecal_pt"),
        to_float(gen.get("gen_pt"), 0.0),
    )
    branches["genEta"][0] = to_float(
        gen.get("gen_ecal_eta"),
        to_float(gen.get("gen_eta"), -999.0),
    )
    branches["genPhi"][0] = to_float(
        gen.get("gen_ecal_phi"),
        to_float(gen.get("gen_phi"), -999.0),
    )

    branches["gen_rct_card"][0] = to_int(gen.get("gen_rct_card"), -1)
    branches["gen_crystal_iEta"][0] = to_int(gen.get("gen_crystal_iEta"), -999)
    branches["gen_crystal_iPhi"][0] = to_int(gen.get("gen_crystal_iPhi"), -999)
    branches["gen_local_iEta"][0] = to_int(gen.get("gen_local_iEta"), -999)
    branches["gen_local_iPhi"][0] = to_int(gen.get("gen_local_iPhi"), -999)


def fill_rct_match_branches(branches, cluster):
    branches["rct_matchPass"][0] = 1

    branches["rct_cPt"][0] = cluster["pt"]
    branches["rct_cEta"][0] = cluster["eta"]
    branches["rct_cPhi"][0] = cluster["phi"]
    branches["rct_deltaR"][0] = cluster["deltaR"]

    branches["rct_et2x5"][0] = cluster["et2x5"]
    branches["rct_et5x5"][0] = cluster["et5x5"]

    branches["rct_clusterIdx"][0] = cluster["index"]
    branches["rct_rawEnergy"][0] = cluster["raw_energy"]
    branches["rct_seedEnergy"][0] = cluster["seed_pt"]

    branches["rct_hwEta"][0] = cluster["rct_eta_hw"]
    branches["rct_hwPhi"][0] = cluster["rct_phi_hw"]

    branches["rct_local_iEta"][0] = cluster["local_ieta"]
    branches["rct_local_iPhi"][0] = cluster["local_iphi"]
    branches["rct_global_iEta"][0] = cluster["global_ieta"]
    branches["rct_global_iPhi"][0] = cluster["global_iphi"]
    branches["rct_card"][0] = cluster["card"]


def process_event_dir(event_dir, tree, branches, energy_lsb, max_delta_r, match_only_gen_card):
    gen_csv = find_gen_csv(event_dir)

    if gen_csv is None:
        print(f"No GEN CSV found in {event_dir}")
        return 0, 0, 0

    gen_rows = read_csv_dicts(gen_csv)

    clusters_by_card = {}
    all_clusters = None

    n_gen_total = 0
    n_gen_in_acceptance = 0
    n_matched = 0

    for gen in gen_rows:
        n_gen_total += 1

        reset_branches(branches)
        fill_gen_branches(branches, gen)

        gen_card = branches["gen_rct_card"][0]
        gen_eta = branches["genEta"][0]

        in_rct_acceptance = (
            0 <= gen_card < N_CARDS
            and abs(gen_eta) < ECAL_ETA_RANGE
        )

        if not in_rct_acceptance:
            print(
                f"[OUTSIDE RCT ACCEPTANCE] "
                f"event={branches['event'][0]} "
                f"genIdx={branches['gen_idx'][0]} "
                f"genEta={gen_eta:.5f} "
                f"genPhi={branches['genPhi'][0]:.5f} "
                f"genCard={gen_card}"
            )

            tree.Fill()
            continue

        n_gen_in_acceptance += 1

        if match_only_gen_card:
            if gen_card not in clusters_by_card:
                clusters_by_card[gen_card] = read_ip3_rct_clusters(
                    event_dir,
                    gen_card,
                    energy_lsb=energy_lsb,
                )

            clusters_to_match = clusters_by_card[gen_card]

        else:
            if all_clusters is None:
                all_clusters = []

                for card in range(N_CARDS):
                    all_clusters.extend(
                        read_ip3_rct_clusters(
                            event_dir,
                            card,
                            energy_lsb=energy_lsb,
                        )
                    )

                all_clusters.sort(
                    key=lambda c: c["pt"],
                    reverse=True,
                )

            clusters_to_match = all_clusters

        best, nearest = match_gen_to_rct_cluster(
            gen,
            clusters_to_match,
            max_delta_r=max_delta_r,
        )

        if best is not None:
            n_matched += 1
            fill_rct_match_branches(branches, best)

        tree.Fill()

    return n_gen_total, n_gen_in_acceptance, n_matched

def match_gen_to_rct_cluster(gen_row, clusters, max_delta_r):
    gen_eta = to_float(
        gen_row.get("gen_ecal_eta"),
        to_float(gen_row.get("gen_eta"), -999.0),
    )

    gen_phi = to_float(
        gen_row.get("gen_ecal_phi"),
        to_float(gen_row.get("gen_phi"), -999.0),
    )

    if (
        gen_eta < -900.0
        or gen_phi < -900.0
        or not math.isfinite(gen_eta)
        or not math.isfinite(gen_phi)
    ):
        return None, None

    nearest = None
    nearest_dr = float("inf")
    matched_clusters = []

    for cluster in clusters:
        dr = delta_r(
            cluster["eta"],
            cluster["phi"],
            gen_eta,
            gen_phi,
        )

        if dr < nearest_dr:
            nearest_dr = dr
            nearest = dict(cluster)
            nearest["deltaR"] = dr

        if dr < max_delta_r:
            candidate = dict(cluster)
            candidate["deltaR"] = dr
            matched_clusters.append(candidate)

    matched_clusters.sort(
        key=lambda c: c["pt"],
        reverse=True,
    )

    best = matched_clusters[0] if matched_clusters else None

    return best, nearest

# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Create old-analyzer-compatible l1NtupleProducer/efficiencyTree "
            "from RCT IP3 CSV dumps using PyROOT only."
        )
    )

    parser.add_argument(
        "--rct-io-dir",
        required=True,
        help="Path to rct_IO directory containing event_* folders.",
    )

    parser.add_argument(
        "--output-root",
        default="analyzer_from_ip3_rct.root",
        help="Output ROOT file.",
    )

    parser.add_argument(
        "--energy-lsb",
        type=float,
        default=0.5,
        help=(
            "Energy conversion from decoded raw clusterEnergy to GeV. "
            "Default 0.5, matching RCT_IO LSB_ENERGY."
        ),
    )

    parser.add_argument(
        "--max-delta-r",
        type=float,
        default=DEFAULT_MATCH_DR,
        help="GEN-to-RCT matching cone in physical eta/phi. Default: 0.2.",
    )

    parser.add_argument(
        "--match-all-cards",
        action="store_true",
        help=(
            "Match against all 24 cards, more like the old analyzer looping over all clusters. "
            "Default is to match only against gen_rct_card."
        ),
    )

    args = parser.parse_args()

    ROOT.gROOT.SetBatch(True)

    rct_io_dir = Path(args.rct_io_dir)

    if not rct_io_dir.exists():
        raise RuntimeError(f"Input directory does not exist: {rct_io_dir}")

    event_dirs = sorted(
        p for p in rct_io_dir.iterdir()
        if p.is_dir() and p.name.startswith("event_")
    )

    print(f"[INFO] Found {len(event_dirs)} event directories")
    print(f"[INFO] Output ROOT: {args.output_root}")
    print(f"[INFO] Energy LSB: {args.energy_lsb}")
    print(f"[INFO] Matching Delta R: {args.max_delta_r}")

    if args.match_all_cards:
        print("Matching against all cards")
    else:
        print("Matching only against gen_rct_card")

    fout, tree, branches = create_output_tree(args.output_root)

    total_gen = 0
    total_gen_in_acceptance = 0
    total_matched = 0

    for event_dir in event_dirs:
        n_gen, n_gen_in_acceptance, n_matched = process_event_dir(
        event_dir,
        tree,
        branches,
        energy_lsb=args.energy_lsb,
        max_delta_r=args.max_delta_r,
        match_only_gen_card=(not args.match_all_cards),
        )

        total_gen += n_gen
        total_gen_in_acceptance += n_gen_in_acceptance
        total_matched += n_matched

        print(
            f"{event_dir.name}: "
            f"GEN electrons = {n_gen}, "
            f"in RCT acceptance = {n_gen_in_acceptance}, "
            f"matched = {n_matched}"
        )

    fout.cd("l1NtupleProducer")
    tree.Write()
    fout.Close()

    print("DONE.")
    print(f"Output ROOT file: {args.output_root}")
    print(f"Total GEN electrons: {total_gen}")
    print(f"Total GEN electrons in RCT acceptance: {total_gen_in_acceptance}")
    print(f"Total matched electrons: {total_matched}")

    if total_gen > 0:
        print(
            "Inclusive match fraction: "
            f"{float(total_matched) / float(total_gen):.4f}"
        )

    if total_gen_in_acceptance > 0:
        print(
            "RCT-acceptance match efficiency: "
            f"{float(total_matched) / float(total_gen_in_acceptance):.4f}"
        )


if __name__ == "__main__":
    main()