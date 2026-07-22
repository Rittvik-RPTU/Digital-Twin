---
usage: SI, ScalarValues
name: VehicleValidationModel
description: Vehicle Validation Model with Attribute Bounds
title: Vehicle Validation Model
maintainer: Admin
---

# Vehicle Validation Model

```SysMLv2
package VehicleValidationModel {
    import ScalarValues::*;
 
    part def VehicleTwin {
       
        attribute speed : Real {
            doc /* Vehicle speed in km/h */
            attribute lowerBound : Real := 0.0;
            attribute upperBound : Real := 250.0;
        }
        
        attribute temperature : Real {
            doc /* Battery temperature in Celsius */
            attribute lowerBound : Real := -20.0;
            attribute upperBound : Real := 85.0;
        }
        
        attribute chargeLevel : Real {
            doc /* Battery State of Charge (SoC) percentage */
            attribute lowerBound : Real := 0.0;
            attribute upperBound : Real := 100.0;
        }
    }
    
    part vehicle1 : VehicleTwin;
}
```
