from input_output import SurfBoard, Outputs

class Supervisor:
    
    def __init__(self):
        pass

    def check(self, output : Outputs, surf_board : SurfBoard):

        if(self.is_valid(output)):

            return (output, True)
        
        else:
            
            return (output, False)
    
    def is_valid(self, output : Outputs) -> bool:

        

        return True