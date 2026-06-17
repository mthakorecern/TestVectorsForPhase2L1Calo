#!/usr/bin/env python3

import ROOT
import os
import sys
from typing import List


def set_tdr_style():

    ROOT.gStyle.SetCanvasBorderMode(0)
    ROOT.gStyle.SetCanvasColor(ROOT.kWhite)
    ROOT.gStyle.SetCanvasDefH(800)
    ROOT.gStyle.SetCanvasDefW(1000)
    ROOT.gStyle.SetCanvasDefX(100)
    ROOT.gStyle.SetCanvasDefY(20)

    ROOT.gStyle.SetPadBorderMode(0)
    ROOT.gStyle.SetPadColor(ROOT.kWhite)
    ROOT.gStyle.SetPadGridX(False)
    ROOT.gStyle.SetPadGridY(False)
    ROOT.gStyle.SetGridColor(0)
    ROOT.gStyle.SetGridStyle(3)
    ROOT.gStyle.SetGridWidth(1)

    ROOT.gStyle.SetFrameBorderMode(0)
    ROOT.gStyle.SetFrameBorderSize(1)
    ROOT.gStyle.SetFrameFillColor(0)
    ROOT.gStyle.SetFrameFillStyle(0)
    ROOT.gStyle.SetFrameLineColor(1)
    ROOT.gStyle.SetFrameLineStyle(1)
    ROOT.gStyle.SetFrameLineWidth(1)

    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetOptTitle(0)

    ROOT.gStyle.SetTitleFont(42, "XYZ")
    ROOT.gStyle.SetTitleSize(0.06, "XYZ")
    ROOT.gStyle.SetLabelFont(42, "XYZ")
    ROOT.gStyle.SetLabelSize(0.045, "XYZ")

    ROOT.gStyle.SetPadTopMargin(0.08)
    ROOT.gStyle.SetPadBottomMargin(0.13)
    ROOT.gStyle.SetPadLeftMargin(0.13)
    ROOT.gStyle.SetPadRightMargin(0.05)

    ROOT.gROOT.ForceStyle()


def apply_smaller_leg_style(leg):
    leg.SetBorderSize(0)
    leg.SetFillColor(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(42)
    leg.SetTextSize(0.035)


def get_graph_x_range(graphs):
    xmin = 1e9
    xmax = -1e9

    for graph in graphs:
        for i in range(graph.GetN()):
            x = ROOT.Double(0.0) if hasattr(ROOT, "Double") else None
            y = ROOT.Double(0.0) if hasattr(ROOT, "Double") else None

            if x is not None:
                graph.GetPoint(i, x, y)
                xi = float(x)
            else:
                from array import array
                xarr = array("d", [0.0])
                yarr = array("d", [0.0])
                graph.GetPoint(i, xarr, yarr)
                xi = float(xarr[0])

            ex_low = graph.GetErrorXlow(i)
            ex_high = graph.GetErrorXhigh(i)

            xmin = min(xmin, xi - ex_low)
            xmax = max(xmax, xi + ex_high)

    return xmin, xmax


def apply_smaller_leg_style(leg):
    leg.SetBorderSize(0)
    leg.SetFillColor(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(42)
    leg.SetTextSize(0.035)


def plot_n_efficiencies(
    graphs,
    labels,
    colors,
    x_axis_label,
    legend_name,
    output_name,
    output_dir,
):
    assert len(graphs) == len(labels)
    assert len(graphs) == len(colors)

    if not graphs:
        raise RuntimeError("No efficiency graphs were provided.")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    set_tdr_style()

    canvas = ROOT.TCanvas(
        "Tcan",
        "",
        100,
        20,
        1000,
        800,
    )

    legend = ROOT.TLegend(
        0.55,
        0.15,
        0.90,
        0.45,
    )

    apply_smaller_leg_style(legend)

    canvas.SetGrid()
    canvas.SetFillColor(0)
    canvas.cd()

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextFont(42)
    latex.SetTextColor(ROOT.kBlack)

    for graph, color in zip(graphs, colors):
        graph.SetMarkerColor(color)
        graph.SetMarkerStyle(ROOT.kFullCircle)
        graph.SetLineWidth(2)
        graph.SetLineColor(color)

    # Equivalent of:
    # histDummy = new TGraphAsymmErrors(**itGraph);
    hist_dummy = graphs[0].Clone(
        f"histDummy_{output_name}"
    )

    hist_dummy.SetMarkerColor(0)
    hist_dummy.SetLineColor(0)

    hist_dummy.Draw("AP")

    for graph in graphs:
        graph.Draw("LP SAME")

    hist_dummy.GetXaxis().SetTitle(x_axis_label)
    hist_dummy.GetYaxis().SetTitle("L1 Efficiency")
    hist_dummy.GetXaxis().SetTitleSize(0.06)
    hist_dummy.GetYaxis().SetRangeUser(0.0, 1.5)

    for graph, label in zip(graphs, labels):
        legend.AddEntry(graph, label, "LP")

    legend.Draw()

    emu_label = (
        "#scale[1.0]{#bf{CMS}} "
        "#scale[0.8]{#it{Phase 2 GCT simulation}}"
    )

    if "RCT" in output_name:
        emu_label = (
            "#scale[1.0]{#bf{CMS}} "
            "#scale[0.8]{#it{Phase 2 RCT emulator}}"
        )

    latex.DrawLatex(
        0.16,
        0.960,
        emu_label,
    )

    latex.DrawLatex(
        0.76,
        0.960,
        "#scale[0.8]{14 TeV (200 PU)}",
    )

    latex.DrawLatex(
        0.20,
        0.840,
        "#scale[0.8]{Work in progress}",
    )

    canvas.Update()
    canvas.RedrawAxis()


    png_path = os.path.join(
        output_dir,
        output_name + ".png",
    )

    canvas.SaveAs(png_path)

    canvas.Close()