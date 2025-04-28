import pygame
import sys
import time
from collections import deque
import math 

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (200, 200, 200)
GREEN = (0, 180, 0) 
BLUE = (100, 100, 255) 
PURPLE = (128, 0, 128) 
ORANGE = (255, 165, 0) 
CYAN = (0, 255, 255)   
RED = (255, 0, 0)     
BUTTON_COLOR = (70, 70, 150)
BUTTON_HOVER_COLOR = (100, 100, 180)
BUTTON_TEXT_COLOR = WHITE


MENU_BUTTON_WIDTH = 150
MENU_BUTTON_HEIGHT = 50
SOLVER_BUTTON_WIDTH = 100
SOLVER_BUTTON_HEIGHT = 40
CELL_SIZE = 40 
GRID_MARGIN = 50


PLAY_DELAY_MS = 150 


class Maze:
    def __init__(self, m, n, start_pos, goal_pos, grid):
        self.m = m
        self.n = n
        self.start_pos = start_pos 
        self.goal_pos = goal_pos   
        self.grid = grid

    def get_jump_value(self, pos):
        r, c = pos
        if 0 <= r < self.m and 0 <= c < self.n:
            return self.grid[r][c]
        return 0 

    def is_valid(self, pos):
        r, c = pos
        return 0 <= r < self.m and 0 <= c < self.n

    def get_neighbors(self, pos):
        r, c = pos
        jump_value = self.get_jump_value(pos)
        neighbors = []

        if jump_value == 0: 
            return []

        moves = [
            (r - jump_value, c), 
            (r + jump_value, c), 
            (r, c - jump_value), 
            (r, c + jump_value), 
        ]

        for next_pos in moves:
            if self.is_valid(next_pos):
                neighbors.append(next_pos)
        return neighbors

class SolverState:
    def __init__(self, current_node, path, frontier, visited, final_path=None, message=""):
        self.current_node = current_node 
        self.path_to_current = path 
        self.frontier = set(frontier) 
        self.visited = set(visited) 
        self.final_path = final_path 
        self.message = message 

class Solver:
    def __init__(self, maze):
        self.maze = maze
        self.history = []
        self.current_step_index = -1
        self.solution_path = None
        self.message = ""
        self.visited = set()

    def step(self):
        raise NotImplementedError

    def run_all(self):
        while self.step():
            pass

    def get_current_state(self):
        if 0 <= self.current_step_index < len(self.history):
            return self.history[self.current_step_index]
        return None

    def next_step(self):
        if self.current_step_index < len(self.history) - 1:
            self.current_step_index += 1
            return True
        return False

    def prev_step(self):
        if self.current_step_index > 0:
            self.current_step_index -= 1
            return True
        return False

    def reset(self):
        self.history = []
        self.current_step_index = -1
        self.solution_path = None
        self.message = ""
        self.visited = set()
        self._initialize_search() 

    def _initialize_search(self):
        raise NotImplementedError

    def _record_state(self, current_node, path, frontier_nodes, visited_nodes, message=""):
        frontier_pos = set()
        if frontier_nodes:
             if isinstance(frontier_nodes, deque): 
                 frontier_pos = {item[0] for item in frontier_nodes}
             elif isinstance(frontier_nodes, list): 
                 frontier_pos = {item[0] for item in frontier_nodes}

        state = SolverState(current_node, path, frontier_pos, set(visited_nodes), self.solution_path, message)
        self.history.append(state)

class DFSSolver(Solver):
    def __init__(self, maze):
        super().__init__(maze)
        self._initialize_search()

    def _initialize_search(self):
        self.stack = [(self.maze.start_pos, [self.maze.start_pos])] 
        self.visited = {self.maze.start_pos}
        self._record_state(None, [], [item[0] for item in self.stack], set()) 

    def step(self):
        if not self.stack:
            if not self.solution_path: 
                 self.message = "No hay solución"
                 self._record_state(None, [], [], self.visited, self.message)
                 self.current_step_index = len(self.history) -1 
            return False 

        current_pos, path = self.stack.pop()
        self.visited.add(current_pos) 

        if current_pos == self.maze.goal_pos:
            self.solution_path = path
            self.message = f"Solución encontrada en: {len(path) - 1} movimientos"
            self._record_state(current_pos, path, [item[0] for item in self.stack], self.visited, self.message)
            self.current_step_index = len(self.history) - 1 
            self.stack.clear() 
            return False 

        self._record_state(current_pos, path, [item[0] for item in self.stack], self.visited)

        neighbors = self.maze.get_neighbors(current_pos)
        added_to_stack = False
        for neighbor in reversed(neighbors): 
            if neighbor not in self.visited:
                self.stack.append((neighbor, path + [neighbor]))
                added_to_stack = True

        return True 


class UCSSolver(Solver): 
    def __init__(self, maze):
        super().__init__(maze)
        self._initialize_search()

    def _initialize_search(self):
        self.queue = deque([(self.maze.start_pos, [self.maze.start_pos])]) 
        self.visited = {self.maze.start_pos} 
        self._record_state(None, [], [item[0] for item in self.queue], set(self.visited)) 


    def step(self):
        if not self.queue:
            if not self.solution_path: 
                 self.message = "No hay solución"
                 self._record_state(None, [], [], self.visited, self.message)
                 self.current_step_index = len(self.history) -1 
            return False 

        current_pos, path = self.queue.popleft()

        if current_pos == self.maze.goal_pos:
            self.solution_path = path
            self.message = f"Solución encontrada en: {len(path) - 1} movimientos"
            self._record_state(current_pos, path, [item[0] for item in self.queue], self.visited, self.message)
            self.current_step_index = len(self.history) - 1 
            self.queue.clear()
            return False 

        self._record_state(current_pos, path, [item[0] for item in self.queue], self.visited)

        neighbors = self.maze.get_neighbors(current_pos)
        added_to_queue = False
        for neighbor in neighbors:
            if neighbor not in self.visited:
                self.visited.add(neighbor) 
                self.queue.append((neighbor, path + [neighbor]))
                added_to_queue = True

        return True 

def parse_input_file(filename):
    mazes = []
    try:
        with open(filename, 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                parts = list(map(int, line.split()))
                if not parts or parts == [0]:
                    break
                if len(parts) != 6:
                    print(f"Warning: Cabecera invalida: {line.strip()}.")
                    continue

                m, n, start_r, start_c, goal_r, goal_c = parts
                if m <= 0 or n <= 0:
                    print(f"Warning: Dimension invalida m={m}, n={n}. Saltando laberinto.")
                    continue

                grid = []
                try:
                    for _ in range(m):
                        grid_line = f.readline()
                        row = list(map(int, grid_line.split()))
                        if len(row) != n:
                            raise ValueError(f"Numero de columnas incorrectas. Se esperaban {n}, y se tienen {len(row)}.")
                        grid.append(row)
                except Exception as e:
                    print(f"Error al leer el area de trabajo: {e}. Saltando laberinto.")
                    continue 

                start_pos = (start_r, start_c)
                goal_pos = (goal_r, goal_c)

                if not (0 <= start_r < m and 0 <= start_c < n):
                     print(f"Warning: Posicion de inicio {start_pos} fuera de rango {m}x{n} grid. Saltando laberinto.")
                     continue
                if not (0 <= goal_r < m and 0 <= goal_c < n):
                     print(f"Warning: Posicion final {goal_pos} fuera de rango {m}x{n}. Saltando laberinto.")
                     continue

                mazes.append(Maze(m, n, start_pos, goal_pos, grid))

    except FileNotFoundError:
        print(f"Error: Archivo '{filename}' no encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"Ocurrio un error leyendo el documento: {e}")
    return mazes


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = font
        self.is_hovered = False

    def draw(self, screen):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect, border_radius=5)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered


def draw_menu(screen, mazes, selected_maze_index, selected_algo, font, buttons):
    screen.fill(DARK_GRAY)
    title_font = pygame.font.SysFont(None, 60)
    title_surf = title_font.render("Laberinto Saltarín", True, WHITE)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 80))
    screen.blit(title_surf, title_rect)

    if mazes:
        maze_text = f"Maze {selected_maze_index + 1} ({mazes[selected_maze_index].m}x{mazes[selected_maze_index].n})"
        maze_font = pygame.font.SysFont(None, 40)
        maze_surf = maze_font.render(maze_text, True, WHITE)
        maze_rect = maze_surf.get_rect(center=(WIDTH // 2, 180))
        screen.blit(maze_surf, maze_rect)
        buttons["prev_maze"].draw(screen)
        buttons["next_maze"].draw(screen)
    else:
        no_maze_font = pygame.font.SysFont(None, 40)
        no_maze_surf = no_maze_font.render("No se cargo el laberinto", True, RED)
        no_maze_rect = no_maze_surf.get_rect(center=(WIDTH // 2, 180))
        screen.blit(no_maze_surf, no_maze_rect)


    algo_label_font = pygame.font.SysFont(None, 35)
    algo_label_surf = algo_label_font.render("Seleccione el Algoritmo a usar:", True, WHITE)
    algo_label_rect = algo_label_surf.get_rect(center=(WIDTH // 2, 270))
    screen.blit(algo_label_surf, algo_label_rect)

    buttons["dfs"].draw(screen)
    buttons["ucs"].draw(screen)

    if selected_algo == "DFS":
        pygame.draw.rect(screen, LIGHT_GRAY, buttons["dfs"].rect, 3)
    elif selected_algo == "UCS":
        pygame.draw.rect(screen, LIGHT_GRAY, buttons["ucs"].rect, 3)

    if mazes and selected_algo:
        buttons["start"].draw(screen)

    
    name = pygame.font.SysFont(None, 30)
    name_surf = name.render("Matías Medina", True, WHITE)
    name_rect = name_surf.get_rect(center=(WIDTH // 1.12, 580))
    screen.blit(name_surf, name_rect)

    pygame.display.flip()


def calculate_grid_params(m, n):
    max_grid_width = WIDTH - 2 * GRID_MARGIN
    max_grid_height = HEIGHT - 2 * GRID_MARGIN - 100 

    cell_size_w = max_grid_width // n
    cell_size_h = max_grid_height // m
    cell_size = min(cell_size_w, cell_size_h, 60) 

    grid_width = n * cell_size
    grid_height = m * cell_size

    offset_x = (WIDTH - grid_width) // 2
    offset_y = (HEIGHT - grid_height - 60) // 2 + 20 

    return cell_size, offset_x, offset_y

def draw_solver_view(screen, maze, solver_state, font, buttons, cell_size, offset_x, offset_y, status_message):
    screen.fill(DARK_GRAY)
    m, n = maze.m, maze.n
    grid_font = pygame.font.SysFont(None, int(cell_size * 0.6))

    for r in range(m):
        for c in range(n):
            rect = pygame.Rect(offset_x + c * cell_size, offset_y + r * cell_size, cell_size, cell_size)
            pos = (r, c)
            cell_color = GRAY
            text_color = BLACK

            is_path = solver_state and solver_state.final_path and pos in solver_state.final_path
            is_visited = solver_state and pos in solver_state.visited
            is_frontier = solver_state and pos in solver_state.frontier
            is_current = solver_state and pos == solver_state.current_node

            if pos == maze.start_pos:
                cell_color = BLUE
                text_color = WHITE
            elif pos == maze.goal_pos:
                cell_color = GREEN
                text_color = WHITE

            if is_visited:
                 cell_color = CYAN
                 text_color = BLACK
            if is_frontier:
                 cell_color = ORANGE
                 text_color = BLACK
            if is_current:
                 cell_color = RED
                 text_color = WHITE
            if is_path:
                 cell_color = PURPLE
                 text_color = WHITE
                 if pos == maze.start_pos: cell_color = (100, 0, 100) 
                 if pos == maze.goal_pos: cell_color = (0, 100, 0)   


            pygame.draw.rect(screen, cell_color, rect)
            pygame.draw.rect(screen, LIGHT_GRAY, rect, 1)

            jump_val = maze.grid[r][c]
            num_surf = grid_font.render(str(jump_val), True, text_color)
            num_rect = num_surf.get_rect(center=rect.center)
            screen.blit(num_surf, num_rect)

    buttons["play"].draw(screen)
    buttons["pause"].draw(screen)
    buttons["back"].draw(screen)
    buttons["next"].draw(screen)
    buttons["menu"].draw(screen)

    status_font = pygame.font.SysFont(None, 30)
    message_to_show = solver_state.message if solver_state and solver_state.message else status_message
    if solver_state and solver_state.final_path:
         message_to_show = f"Solución encontrada en: {len(solver_state.final_path)-1} movimientos" if solver_state.final_path else "No hay solución"
    elif solver_state and solver_state.message == "No hay solución":
         message_to_show = "No hay solución"


    status_surf = status_font.render(message_to_show, True, WHITE)
    button_area_top_y = HEIGHT - 70
    padding_above_buttons = 10 
    status_rect = status_surf.get_rect(midbottom=(WIDTH // 2, button_area_top_y - padding_above_buttons))
    screen.blit(status_surf, status_rect) 

    pygame.display.flip()


def main(filename):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Laberinto Saltarín")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 30) 

    
    mazes = parse_input_file(filename)
    if not mazes:
         print("No se encontraron laberintos válidos en el archivo entregado.")
         pygame.quit()
         sys.exit()

    
    game_state = "menu" 
    selected_maze_index = 0
    selected_algo = None 
    current_maze = mazes[selected_maze_index]
    solver = None
    running = True
    is_playing = False 
    last_step_time = 0
    status_message = "" 

    menu_buttons = {
        "prev_maze": Button(WIDTH // 2 - 150 - 20, 160, 40, 40, "<", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, font),
        "next_maze": Button(WIDTH // 2 + 150 - 20, 160, 40, 40, ">", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, font),
        "dfs": Button(WIDTH // 2 - MENU_BUTTON_WIDTH - 10, 300, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT, "DFS", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, font),
        "ucs": Button(WIDTH // 2 + 10, 300, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT, "UCS (BFS)", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, font),
        "start": Button(WIDTH // 2 - MENU_BUTTON_WIDTH // 2, 400, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT, "Resolver", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, font),
    }

    solver_button_y = HEIGHT - 70
    solver_buttons = {
        "play": Button(GRID_MARGIN, solver_button_y, SOLVER_BUTTON_WIDTH, SOLVER_BUTTON_HEIGHT, "Play", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, font),
        "pause": Button(GRID_MARGIN + SOLVER_BUTTON_WIDTH + 10, solver_button_y, SOLVER_BUTTON_WIDTH, SOLVER_BUTTON_HEIGHT, "Pause", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, font),
        "back": Button(GRID_MARGIN + 2*(SOLVER_BUTTON_WIDTH + 10), solver_button_y, SOLVER_BUTTON_WIDTH, SOLVER_BUTTON_HEIGHT, "Back", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, font),
        "next": Button(GRID_MARGIN + 3*(SOLVER_BUTTON_WIDTH + 10), solver_button_y, SOLVER_BUTTON_WIDTH, SOLVER_BUTTON_HEIGHT, "Next", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, font),
        "menu": Button(WIDTH - GRID_MARGIN - SOLVER_BUTTON_WIDTH, solver_button_y, SOLVER_BUTTON_WIDTH, SOLVER_BUTTON_HEIGHT, "Menu", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, font),
    }

    cell_size, grid_offset_x, grid_offset_y = CELL_SIZE, GRID_MARGIN, GRID_MARGIN

    while running:
        mouse_pos = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if game_state == "menu":
                buttons_to_check = menu_buttons
                if not mazes or not selected_algo:
                    buttons_to_check = {k: v for k, v in menu_buttons.items() if k != "start"}

                for name, button in buttons_to_check.items():
                    button.check_hover(mouse_pos)
                    if button.is_clicked(event):
                        if name == "prev_maze":
                            selected_maze_index = (selected_maze_index - 1) % len(mazes)
                            current_maze = mazes[selected_maze_index]
                        elif name == "next_maze":
                            selected_maze_index = (selected_maze_index + 1) % len(mazes)
                            current_maze = mazes[selected_maze_index]
                        elif name == "dfs":
                            selected_algo = "DFS"
                        elif name == "ucs":
                            selected_algo = "UCS"
                        elif name == "start":
                            if selected_algo:
                                if selected_algo == "DFS":
                                    solver = DFSSolver(current_maze)
                                else: 
                                    solver = UCSSolver(current_maze)
                                cell_size, grid_offset_x, grid_offset_y = calculate_grid_params(current_maze.m, current_maze.n)
                                game_state = "solving"
                                is_playing = False 
                                solver.current_step_index = 0 
                                status_message = "Presione Play o next para iniciar."
                        break 

            elif game_state == "solving":
                buttons_to_check = solver_buttons
                for name, button in buttons_to_check.items():
                    button.check_hover(mouse_pos)
                    if button.is_clicked(event):
                        if name == "play":
                            is_playing = True
                            status_message = "Ejecutando..."
                            last_step_time = current_time 
                        elif name == "pause":
                            is_playing = False
                            status_message = "Pausado, aprete Play or Next."
                        elif name == "back":
                            is_playing = False
                            if solver:
                                solver.prev_step()
                            status_message = "Paso Anterior."
                        elif name == "next":
                            is_playing = False
                            if solver:
                                if solver.current_step_index < len(solver.history) - 1:
                                     solver.next_step()
                                else:
                                     more_steps = solver.step() 
                                     if more_steps:
                                         solver.current_step_index += 1 
                                     else:
                                         is_playing = False 
                            status_message = "Paso Siguiente."

                        elif name == "menu":
                            game_state = "menu"
                            solver = None 
                            selected_algo = None 
                            is_playing = False
                        break 

        if game_state == "solving" and is_playing and solver:
            if current_time - last_step_time > PLAY_DELAY_MS:
                 if solver.current_step_index < len(solver.history) - 1:
                      solver.next_step() 
                 else:
                      more_steps = solver.step() 
                      if more_steps:
                          solver.current_step_index += 1
                      else:
                          is_playing = False
                          status_message = solver.message 

                 last_step_time = current_time


        if game_state == "menu":
            draw_menu(screen, mazes, selected_maze_index, selected_algo, font, menu_buttons)
        elif game_state == "solving":
            current_solver_state = solver.get_current_state() if solver else None
            draw_solver_view(screen, current_maze, current_solver_state, font, solver_buttons,
                             cell_size, grid_offset_x, grid_offset_y, status_message)

        clock.tick(60) 

    pygame.quit()
    sys.exit()


def run_solvers_for_console_output(filename):
     print("-" * 30)
     print("Laberintos:")
     print("-" * 30)
     mazes = parse_input_file(filename)
     if not mazes:
         print("No se cargo laberinto.")
         return

     for i, maze in enumerate(mazes):
         print(f"\n--- Resolviendo laberinto {i+1} ({maze.m}x{maze.n}) ---")

         dfs_solver = DFSSolver(maze)
         dfs_solver.run_all() 
         if dfs_solver.solution_path:
             print(f"DFS: Camino encontrado en {len(dfs_solver.solution_path) - 1} movimientos.")
         else:
             print(f"DFS: No se encontro solución.")

         ucs_solver = UCSSolver(maze)
         ucs_solver.run_all() 
         print("UCS (BFS): ", end="")
         if ucs_solver.solution_path:
             print(f"{len(ucs_solver.solution_path) - 1}") 
         else:
             print("No hay solución")

     print("-" * 30)


if __name__ == '__main__':
    input_file = "input.txt" 
    run_solvers_for_console_output(input_file)

    main(input_file)