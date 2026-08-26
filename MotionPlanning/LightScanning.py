import numpy as np

import MotionPlanning.Movement as Movement

try:
    from api.farinoAPI.fairino.Robot import *
except:
    from Robot import RPC

#TODO: Update Logic on Light Scanning
def lightScanHits(lightData, threshold, portions, hits, accuracyPercent):
    for i, arr in enumerate(lightData): #Want to Track Index and Value 
            percent = len(arr[arr > threshold]) / len(arr)
            portions.append(percent) #Store Portions for Each Move
    
            if percent < accuracyPercent:
                hits.append((i, percent)) #Save Which Moves Had Light (Enough Values)

    print(f"Portions: {portions} --- Hits: {hits}")
