import pygame
import os
import random
import neat

# mudar para False se quiser jogar
ai_jogando = True
geracao = 0

# constantes de tamanho da tela
TELA_LARGURA = 500
TELA_ALTURA = 800

# constantes de imagens
IMAGEM_CANO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'pipe.png')))
IMAGEM_CHAO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
IMAGEM_BACKGROUND = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))
IMAGENS_PASSARO = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird3.png')))
]

# definir uma fonte para os textos
pygame.font.init()
FONTE_PONTOS = pygame.font.SysFont('arial', 50)


class Passaro:
    # imagens do pássaro
    IMGS = IMAGENS_PASSARO
    # animações da rotação
    ROTACAO_MAXIMA = 25
    VELOCIDADE_ROTACAO = 15
    TEMPO_ANIMACAO = 4

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angulo = 0
        self.velocidade = 0  # vertical
        self.altura = self.y
        self.tempo = 0
        self.contagem_imagem = 0
        self.imagem = self.IMGS[0]

    def pular(self):
        self.velocidade = -9.5
        self.tempo = 0
        self.altura = self.y

    def mover(self):
        # calcular o deslocamento
        self.tempo += 1
        # fórmula do sorvetão
        deslocamento = 1.2 * (self.tempo**2) + self.velocidade * self.tempo

        # restringir o deslocamento
        if deslocamento > 16:
            deslocamento = 16
        elif deslocamento < 0:
            deslocamento -= 2

        # deslocar o pássaro
        self.y += deslocamento

        # ângulo do pássaro
        if deslocamento < 0 or self.y < (self.altura - 45):
            if self.angulo < self.ROTACAO_MAXIMA:
                self.angulo = self.ROTACAO_MAXIMA
        else:
            if self.angulo > -60:
                self.angulo -= self.VELOCIDADE_ROTACAO

    def desenhar(self, tela):
        # definir qual imagem do pássaro vai aparecer
        self.contagem_imagem += 1

        if self.contagem_imagem < self.TEMPO_ANIMACAO:
            self.imagem = self.IMGS[0]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*2:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*3:
            self.imagem = self.IMGS[2]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*4:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*4 + 1:
            self.imagem = self.IMGS[0]
            self.contagem_imagem = 0

        # se o pássaro estiver caindo, não bater asa
        if self.angulo <= -80:
            self.imagem = self.IMGS[1]
            self.contagem_imagem = self.TEMPO_ANIMACAO*2

        # desenhar a imagem
        imagem_rotacionada = pygame.transform.rotate(self.imagem, self.angulo)
        pos_centro_imagem = self.imagem.get_rect(topleft=(self.x, self.y)).center
        retangulo = imagem_rotacionada.get_rect(center=pos_centro_imagem)
        tela.blit(imagem_rotacionada, retangulo.topleft)

    # pegar máscara de pixels para a colisão
    def get_mask(self):
        return pygame.mask.from_surface(self.imagem)


class Cano:
    DISTANCIA = 200
    VELOCIDADE = 5

    def __init__(self, x):
        self.x = x
        self.altura = 0
        self.pos_topo = 0
        self.pos_base = 0
        self.CANO_TOPO = pygame.transform.flip(IMAGEM_CANO, False, True)
        self.CANO_BASE = IMAGEM_CANO
        self.passou = False
        self.definir_altura()

    def definir_altura(self):
        self.altura = random.randrange(50, 450)
        self.pos_topo = self.altura - self.CANO_TOPO.get_height()
        self.pos_base = self.altura + self.DISTANCIA

    def mover(self):
        self.x -= self.VELOCIDADE

    def desenhar(self, tela):
        tela.blit(self.CANO_TOPO, (self.x, self.pos_topo))
        tela.blit(self.CANO_BASE, (self.x, self.pos_base))

    def colidir(self, passaro: Passaro):
        # masks
        passaro_mask = passaro.get_mask()
        topo_mask = pygame.mask.from_surface(self.CANO_TOPO)
        base_mask = pygame.mask.from_surface(self.CANO_BASE)

        # distância entre pássaro e canos
        distancia_topo = (self.x - passaro.x, self.pos_topo - round(passaro.y))
        distancia_base = (self.x - passaro.x, self.pos_base - round(passaro.y))

        # colisão
        topo_ponto = passaro_mask.overlap(topo_mask, distancia_topo)
        base_ponto = passaro_mask.overlap(base_mask, distancia_base)

        if base_ponto or topo_ponto:
            return True
        else:
            return False


class Chao:
    VELOCIDADE = 5
    LARGURA = IMAGEM_CHAO.get_width()
    IMAGEM = IMAGEM_CHAO

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.LARGURA

    def mover(self):
        self.x1 -= self.VELOCIDADE
        self.x2 -= self.VELOCIDADE

        # se sair da tela, aparece de novo do outro lado
        if self.x1 + self.LARGURA < 0:
            self.x1 = self.x2 + self.LARGURA
        if self.x2 + self.LARGURA < 0:
            self.x2 = self.x1 + self.LARGURA

    def desenhar(self, tela):
        tela.blit(self.IMAGEM, (self.x1, self.y))
        tela.blit(self.IMAGEM, (self.x2, self.y))


def desenhar_tela(tela, passaros: [Passaro], canos: [Cano], chao: Chao, pontos: int):
    # fundo
    tela.blit(IMAGEM_BACKGROUND, (0, 0))
    # passaros
    for passaro in passaros:
        passaro.desenhar(tela)
    # canos
    for cano in canos:
        cano.desenhar(tela)
    # pontos
    texto = FONTE_PONTOS.render(f"Pontuação: {pontos}", 1, (255, 255, 255))
    tela.blit(texto, (TELA_LARGURA - 10 - texto.get_width(), 10))

    # geração, se for a AI jogando
    if ai_jogando:
        texto = FONTE_PONTOS.render(f"Geração: {geracao}", 1, (255, 255, 255))
        tela.blit(texto, (10, 10))

    # chao
    chao.desenhar(tela)
    # atualizar a tela
    pygame.display.update()


def main(genomas, config):  # fitness function
    # adicionando 1 em geração a cada vez que roda
    global geracao
    geracao += 1
    # criando a tela
    tela = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
    # criando os pássaros com seus genomas e redes neurais
    if ai_jogando:
        redes = []
        lista_genomas = []
        passaros = []
        # pra cada genoma, gerando sua rede neural e seu pássaro
        # genomas é uma lista de tuplas, mas quero usar só o segundo item das tuplas, por isso o underline
        for _, genoma in genomas:
            rede = neat.nn.FeedForwardNetwork.create(genoma, config)
            redes.append(rede)
            genoma.fitness = 0
            lista_genomas.append(genoma)
            passaros.append(Passaro(230, 350))
    # criando um pássaro se for jogar normal
    else:
        passaros = [Passaro(230, 350)]

    chao = Chao(730)
    canos = [Cano(700)]
    pontos = 0
    relogio = pygame.time.Clock()

    rodando = True
    while rodando:
        relogio.tick(30)

        # interação com o usuário
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
                pygame.quit()
                quit()

            if not ai_jogando:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_SPACE:
                        for passaro in passaros:
                            passaro.pular()

        indice_cano = 0
        if len(passaros) > 0:
            # descobrir qual cano olhar
            # se o passaro já passou do canos[0], olhar para canos[1]
            if len(canos) > 1    and    passaros[0].x > (canos[0].x + canos[0].CANO_TOPO.get_width()):
                indice_cano = 1
        else:
            rodando = False
            break

        # mover os pássaros
        if ai_jogando:
            for i, passaro in enumerate(passaros):
                passaro.mover()
                # aumentar o fitness um pouco para recompensar mais aqueles que vão mais longe
                lista_genomas[i].fitness += 0.1
                # ativar a rede neural com os inputs  |  abs transforma o número em absoluto (facilita pra rede)
                output = redes[i].activate((passaro.y,
                                            abs(passaro.y - canos[indice_cano].altura),
                                            abs(passaro.y - canos[indice_cano].pos_base)))
                # output entre -1 e 1... se for > 0.5 pula
                if output[0] > 0.5:
                    passaro.pular()
        else:
            passaros[0].mover()

        # mover o chão
        chao.mover()

        # lógica de colisão e adição de canos
        adicionar_cano = False
        remover_canos = []
        for cano in canos:
            for i, passaro in enumerate(passaros):
                # se o pássaro colidir no cano
                if cano.colidir(passaro):
                    # remover pássaro
                    passaros.pop(i)
                    # penalizar removendo fitness  e  remover genoma e rede lista
                    if ai_jogando:
                        lista_genomas[i].fitness -= 1
                        lista_genomas.pop(i)
                        redes.pop(i)
                if not cano.passou and passaro.x > cano.x:
                    cano.passou = True
                    adicionar_cano = True
            cano.mover()
            if cano.x + cano.CANO_TOPO.get_width() < 0:
                remover_canos.append(cano)

        if adicionar_cano:
            pontos += 1
            canos.append(Cano(600))
            # recompensar pássaros vivos a cada cano adicionado
            if ai_jogando:
                for genoma in lista_genomas:
                    genoma.fitness += 5

        for cano in remover_canos:
            canos.remove(cano)

        # colisão com chão e teto
        for i, passaro in enumerate(passaros):
            if (passaro.y + passaro.imagem.get_height()) > chao.y or passaro.y < 0:
                passaros.pop(i)
                # removendo genoma e rede neural do pássaro morto
                if ai_jogando:
                    lista_genomas.pop(i)
                    redes.pop(i)

        # desenhando a tela
        desenhar_tela(tela, passaros, canos, chao, pontos)


def rodar(caminho_config):
    # pegando as configs da AI
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                caminho_config)

    # criando população inicial de pássaros
    populacao = neat.Population(config)

    populacao.add_reporter(neat.StdOutReporter(True))
    populacao.add_reporter(neat.StatisticsReporter())

    # rodar com a função main e limitar gerações a 50
    if ai_jogando:
        populacao.run(fitness_function=main, n=50)
    else:
        main(None, None)


if __name__ == '__main__':
    rodar('config.txt')
