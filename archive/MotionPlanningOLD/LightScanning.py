import numpy as np

import archive.MotionPlanning.Movement as Movement

try:
    from api.farinoAPI.fairino.Robot import *
except:
    from Robot import RPC

#TODO: Update Logic on Light Scanning
def light_scan_hits(lightData, threshold, portions, hits, accuracyPercent):
    for i, arr in enumerate(lightData): #Want to Track Index and Value 
            percent = len(arr[arr > threshold]) / len(arr)
            portions.append(percent) #Store Portions for Each Move
    
            if percent < accuracyPercent:
                hits.append((i, percent)) #Save Which Moves Had Light (Enough Values)

    print(f"Portions: {portions} --- Hits: {hits}")


def normalize_light_data(data):
    _, intensities, *_ = testData.individualize(data) #testData.result(testData.cur_move_id)        #Get Light Data After Each Move
                                        #Clamp to 0
    
            #Check in Case Clamps All to 0; Normalize per Move
            norm_intensities = np.array(intensities) / max(np.max(intensities),1)
            norm_intensities[norm_intensities < clamp] = 0   
                
            lightData.append(norm_intensities)                             #Append Light Data; List of NumPy arrays  