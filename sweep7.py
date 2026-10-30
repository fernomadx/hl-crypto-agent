"""Sweep focado 7 moedas (HYPE/PUMP/NEAR/ONDO/UNI/SUI/BNB): IS 75% + OOS top."""
import sys; sys.path.insert(0,'.')
import sweep3
sweep3.UNI=['HYPE','PUMP','NEAR','ONDO','UNI','SUI','BNB']
sys.argv=['x','--out','results_7coins.csv']
sweep3.main()
