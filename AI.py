import tetris
import time
from pulp import lpSum
from pulp import LpProblem
from pulp import LpMaximize,LpMinimize
from pulp import LpVariable
from pulp import LpStatus

tetris_shapes = [
	[[1, 1, 1],
	 [0, 1, 0]],
	
	[[0, 1, 1],
	 [1, 1, 0]],
	
	[[1, 1, 0],
	 [0, 1, 1]],
	
	[[1, 0, 0],
	 [1, 1, 1]],
	
	[[0, 0, 1],
	 [1, 1, 1]],
	
	[[1, 1, 1, 1]],
	
	[[1, 1],
	 [1, 1]]
]

def check_collision(board, shape, offset):
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            try:
                if cell and board[ cy + off_y ][ cx + off_x ]:
                    return True
            except IndexError:
                return True
    return False

def remove_row(board, row):
    del board[row]
    return [[0 for i in range(20)]] + board
	
def join_matrixes(mat1, mat2, mat2_off):
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cy+off_y-1	][cx+off_x] += val
    return mat1

def rotate_clockwise(shape):
    return [ [ shape[y][x] for y in range(len(shape)) ] for x in range(len(shape[0]) - 1, -1, -1) ]

class Player:
    def __init__(self):
        self.App = tetris.TetrisApp()
        self.App.run()
        self.r = {}
        self.rows = self.App.get_rows()
        self.cols = self.App.get_cols()
        for i in range(2*self.cols+3):
            self.r["r"+str(i)] = 1
        self.alpha = 0.9
        self.N = 100
        self.M = 10
        self.samples = []
        self.number_stones = self.App.get_number_stones()
    
    def get_height(self,board):
        if board!=None:
            height = [0 for i in range(self.cols)]
            for j in range(self.cols):
                for i in range(self.rows):
                    if board[i][j]==1:
                        height[j] = self.rows-1-i
                        break
                    
            return height
        else:
            return [100 for i in range(self.cols)]
    
    def get_num_holes(self,board):
        if board!=None:
            holes=0
            for j in range(self.cols):
                for i in range(self.rows):
                    if board[i][j]==1:
                        for k in range(i,self.rows):
                            if board[k][j]==0:
                                holes+=1
                        break
            return holes
        else:
            return 1000
    
    def diff_height(self,height):
        diff=[]
        for i in range(1,self.cols):
            diff.append(height[i]-height[i-1])
        return diff
    
    def drop_stone(self,stone,stone_x,stone_y,board):
        while True:
            stone_y += 1
            if check_collision(board,stone,(stone_x, stone_y)):
                board = join_matrixes(board,stone,(stone_x, stone_y))
                while True:
                    for i, row in enumerate(board[:-1]):
                        if 0 not in row:
                            board = remove_row(board, i)
                            break
                    else:
                        break
                break
        
        return board
		
    def game_over(self,board):
        result=[]
        for shape in tetris_shapes:
            stone = shape
            stone_x = int(self.cols / 2 - len(stone[0])/2)
            stone_y = 0
			
            if check_collision(board,stone,(stone_x, stone_y)):
                result.append(1)
            else:
                result.append(0)
        return sum(result)
    
    def rotate_stone(self,stone,stone_x,stone_y,board):
        new_stone = rotate_clockwise(stone)
        return new_stone
    
    def move(self,stone,stone_x,stone_y,board,delta_x):
        new_x = stone_x + delta_x
        if new_x < 0:
            new_x = 0
        if new_x > self.cols - len(stone[0]):
            new_x = self.cols - len(stone[0])
        return new_x
    
    def basis(self,board):
        height = self.get_height(board)
        holes = self.get_num_holes(board)
        diff = self.diff_height(height)
        basis_results = []
        basis_results.append(sum([self.r["r"+str(i)]*height[i] for i in range(self.cols)]))
        basis_results.append(sum([self.r["r"+str(i)]*diff[i-self.cols] for i in range(self.cols,2*self.cols-1)]))
        basis_results.append(self.r["r"+str(2*self.cols-1)]*max(height))
        basis_results.append(self.r["r"+str(2*self.cols)]*holes)
        basis_results.append(self.r["r"+str(2*self.cols+1)]*self.game_over(board)/self.number_stones)
        basis_results.append(self.r["r"+str(2*self.cols+2)])
        return sum(basis_results)
    
    def basis_variable(self,board,cost,variables,x):
        height = self.get_height(board)
        holes = self.get_num_holes(board)
        diff = self.diff_height(height)
        constraint = []
        
        for i in range(self.cols):
            constraint.append(self.alpha*variables[x[i]]*height[i])
        
        for i in range(self.cols-1):
            constraint.append(self.alpha*variables[x[self.cols+i]]*diff[i])
            
        constraint.append(self.alpha*variables[x[2*self.cols-1]]*max(height))
        constraint.append(self.alpha*variables[x[2*self.cols]]*holes)
        constraint.append(self.alpha*variables[x[2*self.cols+1]]*self.game_over(board)/self.number_stones)
        constraint.append(self.alpha*variables[x[2*self.cols+2]])
        constraint.append(cost)
        return constraint
    
    def simulate_steps(self,orig_board,stone,act_stone_x,act_stone_y,iteration,variables,x,direction):
        mini = 1000000
        rot_action = 0
        move_action = 0
        constraints_LHS = []
        for j in range(4):
            stone_x = act_stone_x
            stone_y = act_stone_y
            for i in range(int(self.cols)):
                if not check_collision(orig_board,stone,(stone_x, stone_y)): 
                    new_board = []
                    for a in range(len(orig_board)):
                        temp=[]
                        for b in range(len(orig_board[a])):
                            temp.append(orig_board[a][b])
                        new_board.append(temp)
                    
                    board = self.drop_stone(stone,stone_x,stone_y,new_board)
                    
                    cost = max(self.get_height(board))
                    
                    if iteration%self.M==0:
                        
                        constraint = self.basis_variable(board,cost,variables,x)
                        constraints_LHS.append(constraint)
                    
                    g = cost+self.alpha*self.basis(board)
                    
                    if g<mini:
                        mini=g
                        rot_action=j
                        move_action=direction*i
                
                prev_stone_x = stone_x
                new_board = []
                for a in range(len(orig_board)):
                    temp=[]
                    for b in range(len(orig_board[a])):
                        temp.append(orig_board[a][b])
                    new_board.append(temp)
                stone_x = self.move(stone,stone_x,stone_y,new_board,direction)
                if stone_x == prev_stone_x:
                    break
            new_board = []
            for a in range(len(orig_board)):
                temp=[]
                for b in range(len(orig_board[a])):
                    temp.append(orig_board[a][b])
                new_board.append(temp)
            stone = self.rotate_stone(stone,stone_x,stone_y,new_board)
            
        return rot_action,move_action,mini,constraints_LHS
    
    def play(self):
        x = []
        for i in range(2*self.cols + 3):
            x.append("r"+str(i))
            
        points=0
        prob = LpProblem("LP Solver",LpMaximize)
        variables = LpVariable.dicts("variables",x,lowBound=-10000,upBound=10000,cat='Continuous')
        objective = []
        constraints_number=0
        best_score=0
        while True:
            for iteration in range(1,self.N+1):
                print("iteration number : "+str(iteration))
                orig_stone = self.App.get_stone()
                orig_stone_x = self.App.get_stone_x()
                orig_stone_y = self.App.get_stone_y()
                orig_board = self.App.get_board()
                
                if iteration%self.M==0:                    
                    objective_sample = self.basis_variable(orig_board,0,variables,x)
                    objective.extend(objective_sample)
                    rhs = self.basis_variable(orig_board,0,variables,x)
                
                stone = []
                for a in range(len(orig_stone)):
                    temp=[]
                    for b in range(len(orig_stone[a])):
                        temp.append(orig_stone[a][b])
                    stone.append(temp)
                
                
                rot_action_left,move_action_left,mini_left,constraints_left_LHS = self.simulate_steps(orig_board,stone,orig_stone_x,orig_stone_y,iteration,variables,x,-1)
                constraints_number+=len(constraints_left_LHS)
                for constraint in constraints_left_LHS:
                    prob += lpSum(constraint) >= lpSum(rhs)
                    
                rot_action_right,move_action_right,mini_right,constraints_right_LHS = self.simulate_steps(orig_board,stone,orig_stone_x,orig_stone_y,iteration,variables,x,1)
                constraints_number+=len(constraints_right_LHS)
                for constraint in constraints_right_LHS:
                    prob += lpSum(constraint) >= lpSum(rhs)
                    
                if mini_left < mini_right:
                    rot_action=rot_action_left
                    move_action=move_action_left
                else:
                    rot_action=rot_action_right
                    move_action=move_action_right
                
                left = False
                if move_action<0:
                    left=True
                    move_action*=-1
                
                for i in range(rot_action):
                    self.App.rotate_event()
                    time.sleep(0.1)
                
                for i in range(move_action):
                    if left:
                        self.App.left_event()
                    else:
                        self.App.right_event()
                    time.sleep(0.1)
                
                result,point = self.App.drop_event()
                points+=point
                if not result:
                    if points>best_score:
                        best_score=points
                    self.App.start_event()
                    print("game over. points = "+str(points))
                    points=0
                time.sleep(0.1)
            print("best score until now = "+str(best_score))
            print("solving LP")
            print("number of terms in objective = "+str(len(objective)))
            print("number of constraints = "+str(constraints_number))
            prob += lpSum(objective)
            prob.solve()
            #print(prob)
            print("Status:", LpStatus[prob.status])
            if LpStatus[prob.status]=="Optimal":
                print("updating r values")
                for v in prob.variables():
                    print(v.name, "=", v.varValue)
                    self.r[v.name] = float(v.varValue)

if __name__=="__main__":
    player = Player()
    player.play()