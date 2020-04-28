from random import randrange as rand
import pygame, sys
import numpy as np
from PIL import Image
import cv2

# The configuration
config = {
	'cell_size':	20,
	'cols':		10,
	'rows':		20,
	'delay':	750,
	'maxfps':	30
}

colors = [
(0,   0,   0  ),
(255, 255, 255),
(0,   150, 0  ),
(0,   0,   255),
(255, 120, 0  ),
(255, 255, 0  ),
(180, 0,   255),
(0,   220, 220)
]

# Define the shapes of the single parts
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

def rotate_clockwise(shape):
    return [ [ shape[y][x] for y in range(len(shape)) ] for x in range(len(shape[0]) - 1, -1, -1) ]

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
    return [[0 for i in range(config['cols'])]] + board
	
def join_matrixes(mat1, mat2, mat2_off):
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cy+off_y-1	][cx+off_x] += val
    return mat1

def new_board():
    board = [ [ 0 for x in range(config['cols']) ] for y in range(config['rows']) ]
    board += [[ 1 for x in range(config['cols'])]]
    return board

class TetrisApp(object):
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(250,25)
        self.width = config['cell_size']*config['cols']
        self.height = config['cell_size']*config['rows']
		
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.event.set_blocked(pygame.MOUSEMOTION) # We do not need
		                                             # mouse movement
		                                             # events, so we
		                                             # block them.
        self.init_game()
        self.score = 0
	
    def new_stone(self):
        self.stone = tetris_shapes[rand(len(tetris_shapes))]
        self.stone_x = int(config['cols'] / 2 - len(self.stone[0])/2)
        self.stone_y = 0
		
        if check_collision(self.board,self.stone,(self.stone_x, self.stone_y)):
            self.gameover = True
	
    
    def get_number_stones(self):
        return len(tetris_shapes)
        
    def init_game(self):
        self.board = new_board()
        self.new_stone()
	
    def center_msg(self, msg):
        for i, line in enumerate(msg.splitlines()):
            msg_image =  pygame.font.Font(pygame.font.get_default_font(), 12).render(line, False, (255,255,255), (0,0,0))
		
            msgim_center_x, msgim_center_y = msg_image.get_size()
            msgim_center_x //= 2
            msgim_center_y //= 2
		
            self.screen.blit(msg_image, (self.width // 2-msgim_center_x,self.height // 2-msgim_center_y+i*22))
	
    def draw_matrix(self, matrix, offset):
        off_x, off_y  = offset
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val:
                    pygame.draw.rect(self.screen,colors[val],pygame.Rect((off_x+x) * config['cell_size'],(off_y+y) * config['cell_size'],config['cell_size'],config['cell_size']),0)
	
    def move(self, delta_x):
        if not self.gameover and not self.paused:
            new_x = self.stone_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > config['cols'] - len(self.stone[0]):
                new_x = config['cols'] - len(self.stone[0])
            if not check_collision(self.board,self.stone,(new_x, self.stone_y)):
                self.stone_x = new_x
                
    def quit(self):
        self.center_msg("Exiting...")
        pygame.display.update()
        sys.exit()
	
    def drop(self):
        if not self.gameover and not self.paused:
            lines_cleared=0
            while True:
                self.stone_y += 1
                if check_collision(self.board,self.stone,(self.stone_x, self.stone_y)):
                    self.board = join_matrixes(self.board,self.stone,(self.stone_x, self.stone_y))
                    while True:
                        for i, row in enumerate(self.board[:-1]):
                            if 0 not in row:
                                lines_cleared+=1
                                self.board = remove_row(self.board, i)
                                break
                        else:
                            break
                    self.new_stone()
                    break
            curr_score = 1 + (lines_cleared ** 2) * config['cols']
            self.score += curr_score
            if self.gameover:
                self.score=0
            return curr_score
        return 0
	
    def rotate_stone(self):
        if not self.gameover and not self.paused:
            new_stone = rotate_clockwise(self.stone)
            if not check_collision(self.board,new_stone,(self.stone_x, self.stone_y)):
                self.stone = new_stone
	
    def toggle_pause(self):
        self.paused = not self.paused
	
    def start_game(self):
        if self.gameover:
            self.init_game()
            self.gameover = False
    
    def set_board(self,board):
        self.board = board
    
    def set_stone(self,stone):
        self.stone = stone
    
    def set_stone_x(self,stone_x):
        self.stone_x = stone_x
    
    def set_stone_y(self,stone_y):
        self.stone_y = stone_y
    
    def get_board(self):
        new_board = []
        for i in range(len(self.board)):
            temp=[]
            for j in range(len(self.board[i])):
                temp.append(self.board[i][j])
            new_board.append(temp)
        return new_board
    
    def get_stone(self):
        new_stone = []
        for i in range(len(self.stone)):
            temp=[]
            for j in range(len(self.stone[i])):
                temp.append(self.stone[i][j])
            new_stone.append(temp)
        return self.stone
    
    def get_stone_x(self):
        return self.stone_x
    
    def get_stone_y(self):
        return self.stone_y
	
    def get_rows(self):
        return config['rows']
    
    def get_cols(self):
        return config['cols']
    
    def run(self):
		
        self.gameover = False
        self.paused = False
		
        #pygame.time.set_timer(pygame.USEREVENT+1, config['delay'])
        self.dont_burn_my_cpu = pygame.time.Clock()
        
        self.screen.fill((0,0,0))
        if self.gameover:
            self.center_msg("""Game Over! Press space to continue""")
        else:
            if self.paused:
                self.center_msg("Paused")
            else:
                self.draw_matrix(self.board, (0,0))
                self.draw_matrix(self.stone,(self.stone_x,self.stone_y))
        pygame.display.update()
        
    def render(self):
        '''Renders the current board'''
        img = [colors[p] for row in self.get_board() for p in row]
        img = np.array(img).reshape(config['rows']+1, config['cols'], 3).astype(np.uint8)
        img = img[..., ::-1] # Convert RRG to BGR (used by cv2)
        img = Image.fromarray(img, 'RGB')
        img = img.resize((config['cols'] * 25, config['rows'] * 25))
        img = np.array(img)
        cv2.putText(img, str(self.score), (22, 22), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1)
        cv2.imshow('image', np.array(img))
        cv2.waitKey(1)
        
    def update_screen(self):
        pygame.event.get()
        self.screen.fill((0,0,0))
        font = pygame.font.Font('freesansbold.ttf', 20)
        text = font.render(str(self.score), True, (255,255,255), (0,0,0))
        textRect = text.get_rect()
        textRect.center = (20,10)
        if self.gameover:
            self.center_msg("""Game Over! Press space to continue""")
        else:
            if self.paused:
                self.center_msg("Paused")
            else:
                self.draw_matrix(self.board, (0,0))
                self.draw_matrix(self.stone,(self.stone_x,self.stone_y))
        self.screen.blit(text, textRect)
        pygame.display.update()
        
        self.dont_burn_my_cpu.tick(config['maxfps'])
    
    def drop_event(self,simulate=False):
        points=self.drop()
        if not simulate:
            self.update_screen()
        if self.gameover:
            return False,points
        else:
            return True,points
    
    def quit_event(self,simulate=False):
        self.quit()
        if not simulate:
            self.update_screen()
        
    def left_event(self,simulate=False):
        self.move(-1)
        if not simulate:
            self.update_screen()
        
    def right_event(self,simulate=False):
        self.move(+1)
        if not simulate:
            self.update_screen()
        
    def down_event(self,simulate=False):
        self.drop()
        if not simulate:
            self.update_screen()

    def rotate_event(self,simulate=False):
        self.rotate_stone()
        if not simulate:
            self.update_screen()
        
    def pause_event(self,simulate=False):
        self.toggle_pause()
        if not simulate:
            self.update_screen()
        
    def start_event(self,simulate=False):
        self.start_game()
        if not simulate:
            self.update_screen()

if __name__ == '__main__':
    App = TetrisApp()
    App.run()