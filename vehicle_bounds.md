# Vehicle Bounds Model

```SysMLv2
package VehicleTwinModel {
    import ScalarValues::*;
 
    part def VehicleTwin {
       
        attribute speed : Real {
            doc /* Vehicle speed in km/h */
            attribute lowerBound : Real := 0.0;
            attribute upperBound : Real := 250.0;
        }
        
        attribute temperature : Real {
            doc /* Battery temperature in Celsius */
            attribute min : Real := -20.0;
            attribute max : Real := 85.0;
        }
        
        attribute chargeLevel : Real {
            doc /* Battery State of Charge (SoC) percentage */
            attribute low : Real := 0.0;
            attribute high : Real := 100.0;
        }
    }
    
    part vehicle1 : VehicleTwin;
}
```
