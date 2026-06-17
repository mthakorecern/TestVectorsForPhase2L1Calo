#!/usr/bin/env python3

import ROOT
from array import array


def set_max_error_to_1(graph):
    """
    Exact Python equivalent of setMaxErrorTo1().
    """

    for i in range(graph.GetN()):
        x = array("d", [0.0])
        y = array("d", [0.0])

        graph.GetPoint(i, x, y)

        point_y = float(y[0])

        # C++ GetErrorY() returns the symmetric/average Y error.
        error_y = float(graph.GetErrorY(i))

        error_up = point_y + error_y
        error_low = point_y - error_y

        if error_up > 1.0:
            graph.SetPointEYhigh(
                i,
                max(0.0, 1.0 - point_y),
            )
        elif error_low < 0.0:
            graph.SetPointEYlow(
                i,
                max(0.0, point_y),
            )


def calculate_efficiency(
    variable,
    tree_path,
    root_file_path,
    l1_cut,
    reco_cut,
    low,
    high,
    variable_bin=False,
):
    """
    Direct PyROOT translation of calculateEfficiency.cpp.

    l1_cut:
        Numerator selection.

    reco_cut:
        Denominator selection.
    """

    root_file = ROOT.TFile.Open(root_file_path)

    if not root_file or root_file.IsZombie():
        print(
            f"ERROR: FILE {root_file_path} "
            "NOT FOUND; EXITING"
        )
        return None

    tree = root_file.Get(tree_path)

    if not tree:
        print(
            f"ERROR: Tree {tree_path} "
            "NOT FOUND; EXITING"
        )
        root_file.Close()
        return None

    bins = 20

    xbins = array(
        "f",
        [20, 25, 30, 35, 40, 45, 50, 60, 70, 90, 110],
    )

    n_var_bins = len(xbins) - 1

    # ROOT object names must be unique when the function
    # is called multiple times in one Python process.
    unique_id = str(ROOT.TUUID()).replace("-", "_")

    denom_name = f"Denom_{unique_id}"
    num_name = f"Num_{unique_id}"

    if variable_bin:
        denom = ROOT.TH1F(
            denom_name,
            denom_name,
            n_var_bins,
            xbins,
        )

        num = ROOT.TH1F(
            num_name,
            num_name,
            n_var_bins,
            xbins,
        )

    else:
        denom = ROOT.TH1F(
            denom_name,
            denom_name,
            bins,
            low,
            high,
        )

        num = ROOT.TH1F(
            num_name,
            num_name,
            bins,
            low,
            high,
        )

    denom.Sumw2()
    num.Sumw2()

    # Exact equivalent of:
    # tree->Draw(variable + ">>+Denom", recoCut);
    # tree->Draw(variable + ">>+Num", l1Cut);
    tree.Draw(
    f"{variable}>>{denom_name}",
    reco_cut,
    "goff",
    )

    tree.Draw(
        f"{variable}>>{num_name}",
        l1_cut,
        "goff",
    )

    eff_asym = ROOT.TGraphAsymmErrors()

    eff_asym.Divide(
        num,
        denom,
        "cl=0.683 b(1,1) mode",
    )

    print(f"\nSelection: {l1_cut}")

    for i_bin in range(1, denom.GetNbinsX() + 1):
        low_edge = denom.GetXaxis().GetBinLowEdge(i_bin)
        high_edge = denom.GetXaxis().GetBinUpEdge(i_bin)

        n_den = denom.GetBinContent(i_bin)
        n_num = num.GetBinContent(i_bin)

        print(
            f"bin {i_bin:2d}: "
            f"[{low_edge:5.1f}, {high_edge:5.1f}) "
            f"den={n_den:5.0f}, "
            f"num={n_num:5.0f}"
        )

    # Exact original procedure.
    num.Divide(denom)

    # eff_asym = ROOT.TGraphAsymmErrors(num)

    # set_max_error_to_1(eff_asym)

    # Prevent Python garbage collection.
    denom.SetDirectory(0)
    num.SetDirectory(0)

    eff_asym._num_hist = num
    eff_asym._denom_hist = denom
    eff_asym._root_file = root_file

    return eff_asym