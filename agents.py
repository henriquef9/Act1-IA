
from mesa import Agent


#Classe para a Base:
#São agentes simples e imóveis
class Base(Agent):
    def __init__(self, pos, model):
        super().__init__(model)
        self.pos = pos

#Classe de Obstáculos:
#São agentes simples e imóveis
class ContinuousObstacle(Agent):
    def __init__(self, pos, model):
        super().__init__(model)
        self.pos = pos

#Classe de Recursos
#São agentes simples e imóveis, nesse caso, com valores atribuidos
class Resources(Agent):
    def __init__(self, pos, model, valor):
        super().__init__(model)
        self.pos = pos
        self.valor = valor

#Classe Agente "PAI?"
#Contém os atributos comuns a maioria dos agentes (eu acho :D)
class AgentIA(Agent):
    def __init__(self, pos, model):
        super().__init__(model)
        self.pos = pos
        self.inventory = 0



    #Função de coleta de recursos IMCOMPLETA
    #Cenário faltante: Estruturas antigas exigem 2 agentes!!!!!!!!!
    def collect(self, resources):
        if self.inventory == 0:
            self.inventory += resources.valor
            self.model.grid.remove_agent(resources)

    def deliver(self):
        for obj in self.model.array_points:
            if obj.agent_type is type(self):
                obj.point += self.inventory
                self.inventory = 0


    #Função para verificar agentes vizinhos, buscando recursos (pode melhorar)
    #Falta teste para agente cercado de recursos
    def check_neigbors(self):
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False)
        for neighbor in neighbors:
            if isinstance(neighbor, Resources):
                self.collect(neighbor)
            elif isinstance(neighbor, Base):
                self.deliver()
    def move(self):
        pass


#Agente reativo simples -> Filho do vagabundo de cima
class AgentRS(AgentIA):
    def move(self):
        self.check_neigbors()

        #Função de movimento aleatório simples de uma célula por vez no grid
        #Foi a forma mais burrinha de evitar sobreposição de agentes :D
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        while not self.model.grid.is_cell_empty(new_position):
            new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)


class AgentBE(AgentIA):

    def __init__(self, pos, model, base_pos = None):
        super().__init__(pos,model)
        self.carga = False
        self.memory = {
            "path": {},  
            "agents": {}, 
            "resources": {},
        }

        self.parceiro = None

        # informação da base
        if base_pos is None:
            base_pos = (1, 1)
        self.base_pos = base_pos

    def collect(self, resources):
        self.inventory += resources.valor
        self.carga = True
        self.model.grid.remove_agent(resources)

    def check_neigbors(self):
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False)
        return neighbors

    # retirar não está em uso
    def move(self, possible_steps):

        possible_steps_empty =  [pos for pos in possible_steps if self.model.grid.is_cell_empty(pos)]
        new_position = self.random.choice(possible_steps_empty)

        self.model.grid.move_agent(self, new_position)

    def pathExplorado(self, new_position):

        if self.memory["path"].get(new_position) == "Explorado":
            return True
        
        return False
    
    def pathComRecursos(self, new_position):

        x1, y1 = new_position

        if self.pathExplorado(new_position):
            for x2 in [1,-1]:
                for y2 in [1,-1]:
                    pos = (x1+x2, y1+y2)
                    if not self.memory["resources"].get(pos) is None and self.memory["resources"].get(pos).valor != 50:
                        return True


        return False

    def explorar(self):


        # vizinhos (percepções)
        neighbors = self.check_neigbors() 

        # atualizar modelo
        resources = []
        agents_next = []

        for neighbor in neighbors:
            if isinstance(neighbor, Resources):
                self.memory["resources"][neighbor.pos] = neighbor
                resources.append(neighbor)
            elif isinstance(neighbor, AgentIA):
                self.memory["agents"][neighbor.pos] = neighbor
                if isinstance(neighbor, AgentBE):
                    agents_next.append(neighbor)
            # Se precisar implementa para salvar obstáculos

        #decidi ação 
        resource_escolhido = None

        if len(resources) > 0:
            # pegar recurso de valor 50
            recursos_valor_50 = [r for r in resources if r.valor == 50]
            if recursos_valor_50 and len(agents_next) >= 1:
                # pegar o primeiro recurso com valor 50
                resource_escolhido = recursos_valor_50[0]
                
                #coletar recurso
                # atualizar a gente aux
                # chamar agente aux
                # mandar agente aux a base pelas mesma posições do agente atual
                self.collect(resource_escolhido)
                self.memory["resources"][resource_escolhido.pos] = None

                agente = agents_next[0]
                
                agente.carga = True
                agente.parceiro = self


                return

            else:
                resources_validos = [r for r in resources if r.valor != 50]
                if resources_validos:
                    # pegar o recurso de maior valor (talvez retirar e pegar apenas o primeiro da lista)
                    resource_escolhido = max(resources_validos, key=lambda obj: obj.valor)
                    # agente coletar recurso
                    #self.model.grid.move_agent(self, resource_escolhido.pos)
                    self.collect(resource_escolhido)
                    # Atualizar modelo 
                    self.memory["resources"][resource_escolhido.pos] = None
                    return

        # move agente

        # posições 
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )

        # posições válidas 
        possible_steps_validas =  [pos for pos in possible_steps if self.model.grid.is_cell_empty(pos) and not self.pathExplorado(pos)]

        # verificar se tem posições válidas 
        if possible_steps_validas:
            new_position = self.random.choice(possible_steps_validas)
        else:
            # pegar as posições sem obstáculos (qualquer tipo de agente)
            possible_steps_empty =  [pos for pos in possible_steps if self.model.grid.is_cell_empty(pos)]
            # pegar posições que ele tem conhecimento sobre recursos próximos
            possible_steps_resource =  [pos for pos in possible_steps_empty if self.pathComRecursos(pos)]

            # verificar ser tem posições com recursos
            if possible_steps_resource:
                new_position = self.random.choice(possible_steps_resource)
            else:
                new_position = self.random.choice(possible_steps_empty)

        self.memory["path"][new_position] = "Explorado"
        self.model.grid.move_agent(self, new_position)
            

    def retornar(self):

        if self.pos == self.base_pos:
            # Entregar recurso
            self.carga = False
            # atualizar modelo
            self.memory["path"] = {key: value for key, value in self.memory["path"].items() if value != "Não explorado"}

            # salvar recurso entrege na base 
        else:
            # Caminhar na direção da base
            x, y = self.pos
            bx, by = self.base_pos

            nova_pos = (x + (1 if bx > x else -1 if bx < x else 0),
                        y + (1 if by > y else -1 if by < y else 0))


            if bx != x and by != y:
                if abs(bx - x) > abs(by - y):  # Preferir movimento horizontal
                    nova_pos = (x + (1 if bx > x else -1), y)
                else:  # Preferir movimento vertical
                    nova_pos = (x, y + (1 if by > y else -1))

            # Verificar se posição não tem obstáculos (tá considerando todos os tipos de agent)
            if not self.model.grid.is_cell_empty(nova_pos) or self.memory["path"].get(nova_pos) == "Não explorado":
                possible_steps = self.model.grid.get_neighborhood(
                    self.pos, moore=False, include_center=False
                )
                possible_steps_empty =  [pos for pos in possible_steps if self.model.grid.is_cell_empty(pos)]
                nova_pos = self.random.choice(possible_steps_empty)                
            
            self.memory["path"][nova_pos] = "Não explorado"
            self.model.grid.move_agent(self, nova_pos)
    
    def seguir(self):

        pos_parceiro = self.parceiro.pos

        if pos_parceiro == self.base_pos:
            self.carga = False
            self.parceiro = None
            

        self.model.grid.move_agent(self, pos_parceiro)

    def step(self):
        if self.carga == False:
            self.explorar()
        elif self.carga == True:
            if not self.parceiro is None:
                self.seguir()     
            self.retornar()


class AgentBDI(AgentIA):
    def __init__(self, pos, model):
        super().__init__(pos, model)
        self.waiting = False
        self.moving = False

    def collect(self, resources):
        if self.inventory == 0:
            self.inventory += resources.valor
            self.model.grid.remove_agent(resources)
            self.model.pos_resources.remove(resources)

    def check_neigbors(self):
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False)
        for neighbor in neighbors:
            if isinstance(neighbor, Resources):
                if neighbor not in self.model.pos_resources:
                    self.model.pos_resources.append(neighbor)
                if self.inventory == 0 and neighbor.valor == 50 and self.moving == False:
                    self.waiting = True
                    agents_around = self.model.grid.get_neighbors(neighbor.pos, moore=False, include_center=False)
                    cont = 0
                    for i in agents_around:
                        if isinstance(i, AgentBDI):
                            cont += 1
                    if cont >= 2:
                        self.waiting = False
                        for i in agents_around:
                            if isinstance(i, AgentBDI):
                                i.moving = False
                        self.collect(neighbor)
                if neighbor.valor != 50:
                    self.collect(neighbor)

            elif isinstance(neighbor, Base):
                self.deliver()

    def move(self):
        if not self.waiting:
            possible_steps = self.model.grid.get_neighborhood(
                self.pos, moore=False, include_center=False
            )
            new_position = self.random.choice(possible_steps)
            while not self.model.grid.is_cell_empty(new_position):
                new_position = self.random.choice(possible_steps)
            self.model.grid.move_agent(self, new_position)

    def move_to_pos(self, pos):
        if not self.waiting:
            x_atual, y_atual = self.pos
            x_destino, y_destino = pos

            # Cálculo de direções possíveis
            direcoes = [
                ((x_atual + 1, y_atual), x_atual < x_destino),
                ((x_atual, y_atual + 1), y_atual < y_destino),
                ((x_atual - 1, y_atual), x_atual > x_destino),
                ((x_atual, y_atual - 1), y_atual > y_destino),
            ]

            # Tentar mover na direção mais lógica disponível
            for nova_posicao, condicao in direcoes:
                if condicao and self.model.grid.is_cell_empty(nova_posicao):
                    self.model.grid.move_agent(self, nova_posicao)

                    return

            for i in range(3):
                self.move()




    def priority(self):
        x_atual = self.pos[1]
        y_atual = self.pos[0]
        pos_final = (0,0)
        min_x = 100000
        min_y = 100000

        for i in self.model.pos_resources:
            around_resources = self.model.grid.get_neighbors(i.pos, moore=False, include_center=False)
            for j in around_resources:
                if isinstance(j, AgentBDI) and j.waiting == True:
                    pos_final = i.pos
                    if self.waiting == False:
                        self.moving = True
                    return pos_final

            x_destino = i.pos[1]
            y_destino = i.pos[0]
            if abs(x_atual-x_destino) < min_x and abs(y_atual-y_destino) < min_y:
                min_x = x_destino
                min_y = y_destino
                pos_final = i.pos
        return pos_final


    def check(self):
        self.check_neigbors()
        if self.inventory != 0:
            self.move_to_pos((1,1))
        elif self.model.pos_resources and self.inventory == 0:
            self.move_to_pos(self.priority())
        else:
            self.moving = False
            self.move()
        print("--------------------")
        print("ARRAY DE RECURSOS")
        print(self.model.pos_resources)
        print("--------------------")
        print(self.waiting)
        print(self.moving)
