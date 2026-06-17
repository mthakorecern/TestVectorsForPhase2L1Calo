#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import tempfile
import textwrap

InputFile = "root://cmsxrootd.hep.wisc.edu//store/user/rsimeon/MCFiles/001ebf5f-b83c-43fc-997f-c2e5ecf1f9dd.root"

def running_command(cmd):
    print("Running the following command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

def cmsRunconfigfileproducer(InputFile, OutputFile, Skip_events, Max_events, event_id=None):
    event_block = ""
    if event_id is not None:
        event_block = f'eventsToProcess = cms.untracked.VEventRange("{event_id}"),'

    return textwrap.dedent(f"""
        import FWCore.ParameterSet.Config as cms
                           
        process = cms.Process("COPY")

        process.source = cms.Source(
            "PoolSource",
            fileNames = cms.untracked.vstring("{InputFile}"),
            inputCommands = cms.untracked.vstring(
                "keep *",

                # Drop only the known problematic branch causing the schema mismatch
                "drop l1tTrackerMuons_l1tTkMuonsGmt__HLT"
            ),
            skipEvents = cms.untracked.uint32({Skip_events}),
            {event_block}
        )

        process.maxEvents = cms.untracked.PSet(
            input = cms.untracked.int32({Max_events})
        )

        process.out = cms.OutputModule(
            "PoolOutputModule",
            fileName = cms.untracked.string("{OutputFile}"),
            outputCommands = cms.untracked.vstring(
                "drop *",

                # Keep the normal TP branches
                "keep *_simEcalEBTriggerPrimitiveDigis_*_*",
                "keep *_simHcalTriggerPrimitiveDigis_*_*",

                # Storing the GEN Level Branches
                "keep *_genParticles_*_*",
                "keep *_slimmedJets_*_*",
                "keep *_slimmedGenJets_*_*",
                "keep *_slimmedElectrons_*_*",
                


                # Keep the premix-stage2 TP branches too
                "keep *_DMEcalEBTriggerPrimitiveDigis_*_*",
                "keep *_DMHcalTriggerPrimitiveDigis_*_*",

                # Keep minimal event bookkeeping
                "keep edmTriggerResults_*_*_*",
                "keep edmEventAuxiliary_*_*_*",
                "keep edmMergeableCounter_*_*_*"
            )
        )

        process.end = cms.EndPath(process.out)
        """)


def firsteventorrangeofevents(InputFile, OutputFile, start, count):
    cfg_text = cmsRunconfigfileproducer(
        InputFile=InputFile,
        OutputFile=OutputFile,
        Skip_events=start,
        Max_events=count,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix="_copy_cfg.py", delete=False) as tf:
        tf.write(cfg_text)
        cfg_name = tf.name
    
    try:
        running_command(["cmsRun", cfg_name])
    finally:
        if os.path.exists(cfg_name):
            os.remove(cfg_name)

def copy_specific_event(InputFile, OutputFile, event_id):
    cfg_text = cmsRunconfigfileproducer(
        InputFile=InputFile,
        OutputFile=OutputFile,
        Skip_events=0,
        Max_events=1,
        event_id=event_id,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix="_copy_cfg.py", delete=False) as tf:
        tf.write(cfg_text)
        cfg_name = tf.name
    
    try:
        running_command(["cmsRun", cfg_name])
    finally:
        if os.path.exists(cfg_name):
            os.remove(cfg_name)

def main():
    parser = argparse.ArgumentParser(
        description="Copy one or more EDM events from a ROOT file into a new ROOT file."
    )

    parser.add_argument(
        "-i", "--input-file",
        default=InputFile,
        help="Input EDM ROOT file"
    )
    parser.add_argument(
        "-o", "--output-file",
        default="Output.root",
        help="Output ROOT file"
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--event-id",
        help="Copy one specific event by RUN:LUMI:EVENT, e.g. 1:45:123456"
    )
    mode.add_argument(
        "--range",
        action="store_true",
        help="Copy a range of events by entry position using --start and --count"
    )

    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Starting event entry index for default/range mode (default: 0)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of events to copy in default/range mode (default: 1)"
    )

    args = parser.parse_args()

    if args.start < 0:
        print("Error: --start must be >= 0")
        sys.exit(1)

    if args.count <= 0:
        print("Error: --count must be > 0")
        sys.exit(1)

    try:
        if args.event_id:
            print(f"Copying specific event {args.event_id} -> {args.output_file}")
            copy_specific_event(args.input_file, args.output_file, args.event_id)
        else:
            print(f"Copying events by position: start={args.start}, count={args.count} -> {args.output_file}")
            firsteventorrangeofevents(args.input_file, args.output_file, args.start, args.count)

        print(f"\nDone. Output written to: {args.output_file}")

    except subprocess.CalledProcessError as e:
            print(f"\nCommand failed with exit code {e.returncode}")
            sys.exit(e.returncode)


if __name__ == "__main__":
    main()