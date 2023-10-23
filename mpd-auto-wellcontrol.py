import openlab
import numpy as np

username = "jjvisser@stud.ntnu.no"
apikey = "262718DB6948FD5D7AAC5A1C490A717F8D3ED2763754E9B3C323DFAFFFE422D8"
licenseguid = "c3a0315b-813c-4e0b-8ec9-e14436a1783d"

session = openlab.http_client(username=username, apikey=apikey, licenseguid=licenseguid)

config_name = "MPD Automatic Well Control"

initial_bit_depth = 2500

class piController():
    __uiInit = 0

    def __init__(self, kp, ki, ts):
        self.kp = kp
        self.ki = ki
        self.ts = ts
    

    def reset(self):
        self.uiLast = self.__uiInit

    def getOutput(self, yd, y):
        self.yd = yd/100000
        self.y = y/100000
        self.e = self.yd - self.y
        up = self.kp*self.e
        ui = self.uiLast + self.ki*self.e*self.ts
        # Add saturation function / anti windup 
        self.uiLast = ui
        output = up + ui
        return output
    
# Simulation measurements
tags = ["SPP", "FlowRateOut", "ChokePressure", "ChokeOpening"]

# Initialize simulation
kp = -0.07
ki = -0.0008
sim_name = "FB Linearized P="+str(kp)+"I="+str(ki) + " init choke 10 %"
sim = session.create_simulation(config_name, sim_name, initial_bit_depth, 
                                # influx_type = "based on geopressure",
                                UseReservoirModel=True, ManualReservoirMode=False)
sim.end_simulation_on_exiting = True
timeStep = 1
SIM_TIME = 2000

# Units
FLOW_UNIT_CONV_FACTOR = 1/6e4   # l/min to m^3/s
PRESSURE_CONV_FACTOR = 1e5      # bar to pascal

# Configure simulation time and setpoints
startTime = timeStep
endTime = startTime + SIM_TIME
initialFlowRate = 2500*FLOW_UNIT_CONV_FACTOR
initialChokeOpening = 1
initialBopChokeOpening = 1 
initialMudDensity = 1.33

timeChange = np.array([60, 120, 180, 210, 240])

# PI Controllers
piSPP = piController(kp=kp, ki=ki, ts=1)
piSPP.reset()

# Run the simulation 
for timeStep in range(startTime, endTime):
    if (timeStep >= startTime) and (timeStep < 60):
        flowRateIn = initialFlowRate
        chokeOpening = initialChokeOpening
        bopChokeOpening = initialBopChokeOpening
    if (timeStep >= 60) and (timeStep < 120):
        flowRateIn =  1000*FLOW_UNIT_CONV_FACTOR
        chokeOpening = initialChokeOpening
        bopChokeOpening = initialBopChokeOpening
    if (timeStep >= 120) and (timeStep < 180):
        flowRateIn =  0
        chokeOpening = 0
        bopChokeOpening = 0
    if (timeStep >= 180) and (timeStep < 210):
        flowRateIn =  200*FLOW_UNIT_CONV_FACTOR
        chokeOpening = 0
        bopChokeOpening = 0
    if (timeStep >= 210) and (timeStep < 240):
        flowRateIn =  0
        chokeOpening = 0
        bopChokeOpening = 0
    if (timeStep >= 240) and (timeStep < 260):
        flowRateIn =  1000*FLOW_UNIT_CONV_FACTOR
        chokeOpening = 0
        bopChokeOpening = 0
    if (timeStep >= 260):
    # if (timeStep >= 260) and (timeStep < 1500):
    if (timeStep == 300):
            piSPP.reset()
            flowRateIn =  1000*FLOW_UNIT_CONV_FACTOR
            chokeOpening = sim.results.ChokeOpening[timeStep-1]
            bopChokeOpening = 1
        flowRateIn =  1000*FLOW_UNIT_CONV_FACTOR
        virtualInput = piSPP.getOutput(43*100000, sim.results.SPP[timeStep-1])
        chokeChange = virtualInput/(np.sqrt(sim.results.ChokePressure[timeStep-1]- 1e5))
        chokeOpening = max(0, min(1, chokeChange + sim.results.ChokeOpening[timeStep-1]))
        bopChokeOpening = 1
    # if (timeStep >= 1500):
    #     if (timeStep == 300):
    #         piSPP.reset()
    #         flowRateIn =  1000*FLOW_UNIT_CONV_FACTOR
    #         chokeOpening = sim.results.ChokeOpening[timeStep-1]
    #         bopChokeOpening = 1
    #     flowRateIn =  1000*FLOW_UNIT_CONV_FACTOR
    #     virtualInput = piSPP.getOutput(35*100000, sim.results.SPP[timeStep-1])
    #     chokeChange = virtualInput/(np.sqrt(sim.results.ChokePressure[timeStep-1]- 1e5))
    #     chokeOpening = max(0, min(1, chokeChange + sim.results.ChokeOpening[timeStep-1]))
    #     bopChokeOpening = 1  


    # Update setpoints 
    sim.setpoints.FlowRateIn = flowRateIn
    sim.setpoints.ChokeOpening = chokeOpening
    sim.setpoints.BopChokeOpening = bopChokeOpening
    
    

    # Step simulator
    sim.step(timeStep)       

    # Output simulation results
    sim.get_results(timeStep,tags)

    # Advance the simulation  
    print(timeStep)  
    timeStep = timeStep + 1
