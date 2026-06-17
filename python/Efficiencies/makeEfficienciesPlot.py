#!/usr/bin/env python3

import ROOT

from CalculateEfficiency import calculate_efficiency
from efficiencyHist import plot_n_efficiencies


def make_efficiencies_plot():

    tree_path = "l1NtupleProducer/efficiencyTree"

    root_file_directory = (
        "/afs/hep.wisc.edu/home/mithakor/Public/"
        "L1CaloPhase2/TestVectorsForPhase2/python/"
        "Matching/events_100.root"
    )

    output_directory = (
        "/afs/hep.wisc.edu/home/mithakor/Public/"
        "L1CaloPhase2/TestVectorsForPhase2/python/"
        "Efficiencies"
    )

    # =====================================================
    # Common denominator and numerator selections
    # =====================================================

    # GEN electrons that are inside the Phase-2 RCT barrel
    # acceptance and were assigned to one of the 24 RCT cards.
    gen_cut = (
        "(abs(genEta) < 1.4841)"
        " && (gen_rct_card >= 0)"
        " && (gen_rct_card < 24)"
    )

    # Require an actual GEN-to-RCT match.
    matched_cut = (
        gen_cut
        + " && (rct_matchPass == 1)"
    )

    # Individual L1 threshold selections.
    l1_cut_25 = (
        matched_cut
        + " && (rct_cPt > 25)"
    )

    l1_cut_30 = (
        matched_cut
        + " && (rct_cPt > 30)"
    )

    l1_cut_35 = (
        matched_cut
        + " && (rct_cPt > 35)"
    )

    l1_cut_40 = (
        matched_cut
        + " && (rct_cPt > 40)"
    )

    # =====================================================
    # RCT efficiency versus GEN pT
    # =====================================================

    graphs = []
    labels = []
    colors = []

    # Use the variable bins defined inside calculate_efficiency().
    use_variable_binning = True

    efficiency_25 = calculate_efficiency(
        variable="genPt",
        tree_path=tree_path,
        root_file_path=root_file_directory,
        l1_cut=l1_cut_25,
        reco_cut=gen_cut,
        low=0,
        high=100,
        variable_bin=use_variable_binning,
    )

    graphs.append(efficiency_25)
    labels.append("L1 p_{T} > 25 GeV")
    colors.append(ROOT.kRed)

    # efficiency_30 = calculate_efficiency(
    #     variable="genPt",
    #     tree_path=tree_path,
    #     root_file_path=root_file_directory,
    #     l1_cut=l1_cut_30,
    #     reco_cut=gen_cut,
    #     low=0,
    #     high=100,
    #     variable_bin=use_variable_binning,
    # )

    # graphs.append(efficiency_30)
    # labels.append("L1 p_{T} > 30 GeV")
    # colors.append(ROOT.kGreen + 2)

    # efficiency_35 = calculate_efficiency(
    #     variable="genPt",
    #     tree_path=tree_path,
    #     root_file_path=root_file_directory,
    #     l1_cut=l1_cut_35,
    #     reco_cut=gen_cut,
    #     low=0,
    #     high=100,
    #     variable_bin=use_variable_binning,
    # )

    # graphs.append(efficiency_35)
    # labels.append("L1 p_{T} > 35 GeV")
    # colors.append(ROOT.kBlue)

    # efficiency_40 = calculate_efficiency(
    #     variable="genPt",
    #     tree_path=tree_path,
    #     root_file_path=root_file_directory,
    #     l1_cut=l1_cut_40,
    #     reco_cut=gen_cut,
    #     low=0,
    #     high=100,
    #     variable_bin=use_variable_binning,
    # )

    # graphs.append(efficiency_40)
    # labels.append("L1 p_{T} > 40 GeV")
    # colors.append(ROOT.kBlack)

    plot_n_efficiencies(
        graphs=graphs,
        labels=labels,
        colors=colors,
        x_axis_label="GEN electron p_{T} [GeV]",
        legend_name="Phase-2 RCT",
        output_name="efficiency_genPt_barrel_RCT",
        output_dir=output_directory,
    )

    # =====================================================
    # RCT efficiency versus GEN eta
    # =====================================================

    graphs = []
    labels = []
    colors = []

    use_variable_binning = False

    efficiency_eta_25 = calculate_efficiency(
        variable="genEta",
        tree_path=tree_path,
        root_file_path=root_file_directory,
        l1_cut=l1_cut_25,
        reco_cut=gen_cut,
        low=-1.5,
        high=1.5,
        variable_bin=use_variable_binning,
    )

    graphs.append(efficiency_eta_25)
    labels.append("L1 p_{T} > 25 GeV")
    colors.append(ROOT.kRed)

    # efficiency_eta_30 = calculate_efficiency(
    #     variable="genEta",
    #     tree_path=tree_path,
    #     root_file_path=root_file_directory,
    #     l1_cut=l1_cut_30,
    #     reco_cut=gen_cut,
    #     low=-1.5,
    #     high=1.5,
    #     variable_bin=use_variable_binning,
    # )

    # graphs.append(efficiency_eta_30)
    # labels.append("L1 p_{T} > 30 GeV")
    # colors.append(ROOT.kGreen + 2)

    # efficiency_eta_35 = calculate_efficiency(
    #     variable="genEta",
    #     tree_path=tree_path,
    #     root_file_path=root_file_directory,
    #     l1_cut=l1_cut_35,
    #     reco_cut=gen_cut,
    #     low=-1.5,
    #     high=1.5,
    #     variable_bin=use_variable_binning,
    # )

    # graphs.append(efficiency_eta_35)
    # labels.append("L1 p_{T} > 35 GeV")
    # colors.append(ROOT.kBlue)

    # efficiency_eta_40 = calculate_efficiency(
    #     variable="genEta",
    #     tree_path=tree_path,
    #     root_file_path=root_file_directory,
    #     l1_cut=l1_cut_40,
    #     reco_cut=gen_cut,
    #     low=-1.5,
    #     high=1.5,
    #     variable_bin=use_variable_binning,
    # )

    # graphs.append(efficiency_eta_40)
    # labels.append("L1 p_{T} > 40 GeV")
    # colors.append(ROOT.kBlack)

    plot_n_efficiencies(
        graphs=graphs,
        labels=labels,
        colors=colors,
        x_axis_label="GEN electron #eta",
        legend_name="Phase-2 RCT",
        output_name="efficiency_genEta_barrel_RCT",
        output_dir=output_directory,
    )


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    make_efficiencies_plot()