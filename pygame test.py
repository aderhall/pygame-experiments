import pygame, time, random, pygame.freetype, copy, math

pygame.init()
pygame.display.set_caption("Space Trash Destroyer")

ocra = pygame.freetype.Font('OCRAStd.otf', 30)
socra = pygame.freetype.Font('OCRAStd.otf', 15)

width, height = 1000, 700
backgroundColor = 255, 0, 0

screen = pygame.display.set_mode((width, height))
boundaries = screen.get_rect()

stars = pygame.transform.scale(pygame.image.load("stars.jpeg"), (width, height))

asteroid = pygame.image.load("asteroid.png")

class Objects(pygame.sprite.Group):
    """Stores the in-game objects"""
    def __init__(self):
        pygame.sprite.Group.__init__(self)

class SpaceObject(pygame.sprite.Sprite):
    """Objects in the game"""
    def __init__(self, image, rotate=0, resize=1):
        pygame.sprite.Sprite.__init__(self)
        self.core_image = pygame.transform.rotozoom(pygame.image.load(image), rotate, resize)
        self.image = copy.copy(self.core_image)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.invincible = 0
        self.health = 100
        self.defense = 1
        self.frame = 0
        global object_count
        object_count += 1
    def move(self, x, y):
        self.rect.move_ip((x, y))
    def rotate(self, angle):
        self.image = pygame.transform.rotate(self.core_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)
    def restoreImage(self):
        self.image = copy.copy(self.core_image)
    def activateInvincible(self):
        self.invincible = 3
    def update(self):
        if self.invincible > 0:
            self.invincible -= 1
        if self.health <= 0:
            self.kill()
            global kill_count
            kill_count += 1
    def takeDamage(self, damage):
        if not self.invincible:
            self.health -= damage/self.defense
            self.activateInvincible()
    def die(self):
        self.kill()

class Ship(SpaceObject):
    """Spaceship"""
    def __init__(self, image, rotate=0, resize=1):
        SpaceObject.__init__(self, image, rotate, resize)
        self.health = 100
        self.defense = 1
        self.xvelocity = 0
        self.yvelocity = 0
        self.cooldown = 0
        self.firedelay = 10
        self.orientation = -90
    def update(self):
        SpaceObject.update(self)
        if self.cooldown > 0:
            self.cooldown -= 1
        collision = pygame.sprite.spritecollide(self, objects, False, pygame.sprite.collide_mask)
        if len(collision) > 0:
            self.takeDamage(100)
            for c in collision:
                if isinstance(self, PlayerShip) and not c.invincible and type(c).__name__ == "Asteroid":
                    c.xvelocity = self.xvelocity - c.xvelocity
                c.takeDamage(100)
    def shoot(self):
        bullets.add(Bullet(False if isinstance(self, PlayerShip) else True, self.rect.center[0], self.rect.center[1], self.orientation))
        self.cooldown = self.firedelay

class Enemy(Ship):
    """Enemy NPC spaceship with AI guidance"""
    def __init__(self, image="enemy.png", rotate=0, resize=1):
        Ship.__init__(self, image, rotate, resize)
        self.health = 50
        self.defense = 1
        self.rect.x, self.rect.y = width, random.randint(0, 700)
        self.radius = 10
        self.firedelay = 30
    def update(self):
        Ship.update(self)

        global me
        if me.rect.x > self.rect.x:
            self.xvelocity += 0.2
        else:
            self.xvelocity -= 0.2
        if me.rect.y > self.rect.y:
            self.yvelocity += 0.2
        else:
            self.yvelocity -= 0.2

        if self.xvelocity >= 5:
            self.xvelocity = 5
        if self.xvelocity <= -5:
            self.xvelocity = -5
        if self.xvelocity >= 5:
            self.xvelocity = 5
        if self.xvelocity <= -5:
            self.xvelocity = -5

        if self.rect.x < -self.rect.width or self.rect.x > self.rect.width+width or self.rect.y <-self.rect.height or self.rect.y > self.rect.height + height:
            global kill_count
            kill_count += 1
            self.kill()

        self.orientation = 180+math.degrees(math.atan2(self.xvelocity, self.yvelocity))

        self.rotate(self.orientation)

        if self.cooldown == 0:
            self.shoot()

        self.move(self.xvelocity, self.yvelocity)

class PlayerShip(Ship):
    """Player-controlled spaceship"""
    def __init__(self, image, rotate=0, resize=1):
        Ship.__init__(self, image, rotate, resize)
        self.defense = 10
    def update(self):
        Ship.update(self)
        self.rect.clamp_ip(boundaries)
        collision = pygame.sprite.spritecollide(self, enemies, False, pygame.sprite.collide_mask)
        if len(collision) > 0:
            self.takeDamage(100)
            for c in collision:
                if not c.invincible and type(c).__name__ == "Asteroid":
                    c.xvelocity = self.xvelocity - c.xvelocity
                c.takeDamage(100)

class Bullet(SpaceObject):
    """Base class for bullets"""
    def __init__(self, enemy, x, y, orientation=-90, image="bullet.png"):
        self.enemy = enemy
        self.orientation = orientation+90
        SpaceObject.__init__(self, image, self.orientation)
        self.rect.center = x, y
        self.damage = 100
        self.defense = 0.5
        self.velocity = (30*math.cos(math.radians(self.orientation)), -30*math.sin(math.radians(self.orientation)))
        self.rect.move_ip(self.velocity)
    def update(self):
        SpaceObject.update(self)
        if self.rect.x < -self.rect.width or self.rect.x > self.rect.width+width or self.rect.y <-self.rect.height or self.rect.y > self.rect.height + height:
            global kill_count
            kill_count += 1
            self.kill()
        self.rect.move_ip(self.velocity)
        collision = pygame.sprite.spritecollide(self, objects, False, pygame.sprite.collide_circle)
        hit = False
        for c in collision:
            c.takeDamage(self.damage)
            hit = True
        if self.enemy:
            global me
            if pygame.sprite.collide_mask(self, me):
                me.takeDamage(self.damage)
                hit = True
        else:
            collision = pygame.sprite.spritecollide(self, enemies, False, pygame.sprite.collide_circle)
            for c in collision:
                c.takeDamage(self.damage)
                hit = True
        if hit:
            self.takeDamage(self.damage)

class Asteroid(SpaceObject):
    """Base class for drifting space objects"""
    def __init__(self):
        self.rotation = random.random()*60-30
        self.angularVelocity = random.random()*5-2.5
        self.size = random.random()+0.5
        SpaceObject.__init__(self, "asteroid.png", self.rotation, self.size)
        self.rect.x, self.rect.y = width, random.randint(0, 700)
        self.yvelocity = random.random()*6-3
        self.xvelocity = random.random()*-5-5
        self.health = 10*int(10*self.size)
        self.defense = 2
        self.radius = 50*self.size
    def update(self):
        global score
        SpaceObject.update(self)
        if self.rect.x < -self.rect.width or self.rect.x > self.rect.width+width or self.rect.y <-self.rect.height or self.rect.y > self.rect.height + height:
            global kill_count
            kill_count += 1
            score-=1
            self.kill()

        self.rect.x += self.xvelocity
        self.rect.y += self.yvelocity
        self.rotation += self.angularVelocity
        self.rotate(self.rotation)
        socra.render_to(self.image, (0, 0), str(self.health), (0, 255, 0))
        if not self.alive():
            score += 1
            del self

# User event for diagnostics
PRINT_REPORT = pygame.USEREVENT+1

# User events for enemy generation
SPAWN_ASTEROID = pygame.USEREVENT+2
SPAWN_ENEMY = pygame.USEREVENT+3

# Game tracking variables
object_count = 0
kill_count = 0

# Will store the objects
objects = Objects()
bullets = Objects()
enemies = Objects()

# Create ship controlled by player
me = PlayerShip("spaceship.png", -90, 0.2)

# Send debug report every 5 seconds
#pygame.time.set_timer(PRINT_REPORT, 5000)

# Setup automatic enemy generation
pygame.time.set_timer(SPAWN_ASTEROID, 1000)
pygame.time.set_timer(SPAWN_ENEMY, 2000)

# Game score variable
score = 0

# Game run condition
run = True

load = len(objects)+len(enemies)+len(bullets)

# Main loop
while run:
    # Check event queue
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False
        if e.type == SPAWN_ASTEROID:
            objects.add(Asteroid())
            load = len(objects)+len(enemies)+len(bullets)
        if e.type == SPAWN_ENEMY:
            enemies.add(Enemy())
        if e.type == PRINT_REPORT:
            print("{} – {} / {}".format(len(objects)+len(enemies)+len(bullets), kill_count, object_count))

    # If not told to move, remember that player speed is zero
    me.xvelocity = 0

    # Check for keyboard input
    keys=pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        me.move(-10, 0)
        me.xvelocity = -10
    if keys[pygame.K_RIGHT]:
        me.move(10, 0)
        me.xvelocity = 10
    if keys[pygame.K_DOWN]:
        me.move(0, 10)
    if keys[pygame.K_UP]:
        me.move(0, -10)
    if keys[pygame.K_SPACE] and me.cooldown == 0:
        me.shoot()

    # Graphics

    # Background
    #screen.fill(backgroundColor)
    screen.blit(stars, (0, 0))

    # Objects in space
    objects.update()
    objects.draw(screen)

    enemies.update()
    enemies.draw(screen)

    bullets.update()
    bullets.draw(screen)

    # Player spaceship (kept separate from other objects for collision purposes)
    me.update()
    screen.blit(me.image, me.rect)

    # HUD
    healthdisplay = ocra.render("Health: {}".format(me.health), (0, 255, 0))
    screen.blit(healthdisplay[0], (10, 10))

    scoredisplay = ocra.render("Score: {}".format(score), (0, 255, 0))
    screen.blit(scoredisplay[0], (600, 10))

    screen.blit(socra.render("Load: {}".format(load), (0, 255, 0))[0], (10, 650))

    # Update the screen each frame
    pygame.display.flip()
    #pygame.display.update()
