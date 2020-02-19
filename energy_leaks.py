from readings.readings import PowerReadings

class EnergyLeaks:
    @property
    ######################################################
    # The amount is calculated by looking at the distribution
    # of values.  The energy leak value will be 
    def amount(self):
        p = PowerReadings()