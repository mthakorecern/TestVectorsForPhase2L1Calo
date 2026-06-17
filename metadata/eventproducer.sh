
voms-proxy-init -voms cms -out /tmp/x509up_u10196 -valid 192:00

# python3 TestVectorproducer.py \
#     -i root://cms-xrd-global.cern.ch//store/mc/Phase2Spring24DIGIRECOMiniAOD/TTToSemileptonic_TuneCP5_14TeV-powheg-pythia8/GEN-SIM-DIGI-RAW-MINIAOD/PU200_Trk1GeV_140X_mcRun4_realistic_v4-v2/00000/22b4c974-c204-4495-8ec6-693a845710fd.root  \
#     --range \
#     --start 0   \
#     --count 10   \
#     -o TTToSemileptonic_TuneCP5_14TeV_693a845710fd_10events.root  \
#     &> TTToSemileptonic_TuneCP5_14TeV_693a845710fd_10events.log &

# python3 TestVectorproducer.py \
#     -i root://cms-xrd-global.cern.ch//store/mc/Phase2Spring24DIGIRECOMiniAOD/DoubleElectron_FlatPt-1To100-gun/GEN-SIM-DIGI-RAW-MINIAOD/PU200_Trk1GeV_140X_mcRun4_realistic_v4-v2/2810000/001ebf5f-b83c-43fc-997f-c2e5ecf1f9dd.root  \
#     --range \
#     --start 0   \
#     --count 10   \
#     -o DoubleElectron_FlatPt-1To100-gun_c2e5ecf1f9dd_10events.root  \
#     &> DoubleElectron_FlatPt-1To100-gun_c2e5ecf1f9dd_10events.log &

python3 TestVectorproducer.py \
    -i root://cms-xrd-global.cern.ch//store/mc/Phase2Spring24DIGIRECOMiniAOD/DoubleElectron_FlatPt-1To100-gun/GEN-SIM-DIGI-RAW-MINIAOD/PU200_Trk1GeV_140X_mcRun4_realistic_v4-v2/2810000/001ebf5f-b83c-43fc-997f-c2e5ecf1f9dd.root  \
    --range \
    --start 0   \
    --count 100   \
    -o DoubleElectron_FlatPt-1To100-gun_c2e5ecf1f9dd_100events.root  \
    &> DoubleElectron_FlatPt-1To100-gun_c2e5ecf1f9dd_100events.log &