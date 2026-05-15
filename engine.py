import math
from enum import Enum

class Vector2D:
    x = y = 0

    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y

    def as_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }

    def sqr_magnitude(self):
        return self.x * self.x + self.y * self.y

    def magnitude(self):
        return math.sqrt(self.sqr_magnitude())

    def cross(self, o):
        return self.x * o.y - self.y * o.x

    def __add__(self, o):
        return Vector2D(self.x + o.x, self.y + o.y)

    def __sub__(self, o):
        return Vector2D(self.x - o.x, self.y - o.y)

    def __mul__(self, o):
        return self.x * o.x + self.y * o.y

class Belt:
    length = 0
    pitch = 0
    teeth = 0

    def __init__(self, pitch, length=0, teeth=0):
        self.pitch = pitch
        if (length == 0):
            self.length = teeth * pitch
            self.teeth = teeth
        if (teeth == 0):
            self.teeth = length / pitch
            self.length = length

    def as_dict(self):
        return {
            "length": self.length,
            "pitch": self.pitch,
            "teeth": self.teeth
        }

class Pulley:
    position = None
    radius = 0
    teeth = 0
    ratio = 0

    def __init__(self, position=None, radius=0, teeth=0, ratio=0):
        self.position = position
        self.radius = radius
        self.teeth = teeth
        self.ratio = ratio

    def updateWithPitch(self, pitch):
        if self.radius == 0:
            self.radius = self.teeth * pitch / (2 * math.pi)
        if self.teeth == 0:
            self.teeth = 2 * self.radius * math.pi / pitch

    def as_dict(self):
        return {
            "position": None if self.position is None else self.position.as_dict(),
            "radius": self.radius,
            "teeth": self.teeth,
            "ratio": self.ratio,
        }
    
    def getTangentTo(self, other):
        k = self.radius - other.radius
        r = other.position - self.position
        r_mag = r.magnitude()
        
        x_x = r_mag - k * k / r_mag
        x_x_r = x_x - r_mag
        y_x = 0 if k == 0 else (x_x_r * x_x * (-1 if k < 0 else 1))/math.sqrt(k * k - x_x_r * x_x_r)

        x = (x_x * r.x - y_x * r.y) / r_mag
        y = (x_x * r.y + y_x * r.x) / r_mag

        return Vector2D(x, y)

    def getArcLength(self, tangent1, tangent2):
        angle = math.acos(tangent1 * tangent2 / math.sqrt(tangent1.sqr_magnitude() * tangent2.sqr_magnitude()))
        adjusted_angle = angle if self.radius * tangent1.cross(tangent2) < 0 else 2 * math.pi - angle
        return adjusted_angle * abs(self.radius)

class PPolygon:
    pulleys = []
    belt = None
    sequence = []
    unknown = None
    attribute = 0

    def __init__(self, pulleys, sequence, unknown=None, belt=None):
        self.pulleys = pulleys
        self.belt = belt
        self.sequence = sequence

        self.populatePulleys()

        self.unknown = pulleys[unknown]
        if self.unknown.radius == 0:
            self.attribute = 0
        elif self.unknown.position.x == None:
            self.attribute = 1
        elif self.unknown.position.y == None:
            self.attribute = 2

    def as_dict(self):
        return {
            "belt": self.belt.as_dict(),
            "pulleys": [p.as_dict() for p in self.pulleys]
        }

    def populatePulleys(self):
        for p in self.pulleys:
            p.updateWithPitch(self.belt.pitch)
            if p.radius != 0 and p.ratio != 0:
                self.scalePulleys(p)

    def scalePulleys(self, base):
        for p in self.pulleys:
            if p is not base and p.ratio != 0:
                p.radius = base.radius * (p.ratio / base.ratio)

    def getIdealBeltLength(self):
        tangents = []
        for i in range(len(self.sequence) - 1):
            tangents.append(self.pulleys[self.sequence[i]].getTangentTo(self.pulleys[self.sequence[i + 1]]))
        
        totalArcs = self.pulleys[self.sequence[0]].getArcLength(tangents[len(tangents) - 1], tangents[0])
        for i in range(1, len(self.sequence) - 1):
            totalArcs += self.pulleys[self.sequence[i]].getArcLength(tangents[i - 1], tangents[i])

        return sum([t.magnitude() for t in tangents]) + totalArcs

    def setUnknown(self, value):
        if self.attribute == 0:
            self.unknown.radius = value
            if self.unknown.ratio != 0:
                self.scalePulleys(self.unknown)
        elif self.attribute == 1:
            self.unknown.position.x = value
        elif self.attribute == 2:
            self.unknown.position.y = value

    def solveForUnknown(self):
        if (self.belt.length == 0):
            self.belt.length = self.getIdealBeltLength()
            return
        
        guess = math.e if self.attribute != 0 else max(max([p.radius for p in self.pulleys]), self.belt.length / (2 * math.pi))
        guess = 10
        def getDifference(guess):
            self.setUnknown(guess)
            return self.getIdealBeltLength() - self.belt.length

        lastResult = getDifference(guess)
        for i in range(100):
            guess -= 0.01 * lastResult / (lastResult - getDifference(guess - 0.01))
            lastResult = getDifference(guess)

            if abs(lastResult) < 0.01:
                self.populatePulleys()
                return

polygon = PPolygon(
    [
        Pulley(position=Vector2D(0, 0), ratio=3),
        Pulley(position=Vector2D(167, 0), ratio=1)
    ],
    [0, 1, 0],
    unknown=1,
    belt=Belt(pitch=5, length=655)
)

polygon.solveForUnknown()
print(polygon.as_dict())

