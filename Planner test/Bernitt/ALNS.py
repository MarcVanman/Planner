class ALNS:
    def __init__(self, DataObject):
        self.Data = DataObject
        
    def Run(runLenght):
        start_time = datetime.now()
        max_sec = start_time + timedelta(seconds= 1000*runlenght)
        print("Start")

        self.Data.generate_initial_solution()

        while((datetime.now() < max_sec):
              # Run the algorithm
              
              # 1: Select destroy and repair methods
              # 2: Compute new solution given above methods
              # 3: If accept(x_temporary, x) then x = x_temporary
              # 4: If c(x_temporary) < c(x_best) then x_best = x_temporary
              # 5: update rho- and rho+ (probabilities for selecting the different destroy/repair)
              