import ResMgr

def raiseWrongXml(xmlContext, subsectionName, msg):
    fileName = subsectionName
    while xmlContext is not None:
        fileName = xmlContext[1] + ('/' + fileName if fileName else '')
        xmlContext = xmlContext[0]

    raise Exception, "error in '" + fileName + "': " + msg
    return


def raiseWrongSection(xmlContext, subsectionName):
    raiseWrongXml(xmlContext, '', "subsection '%s' is missing or wrong" % subsectionName)


def getChildren(xmlCtx, section, subsectionName):
    subsection = section[subsectionName]
    if subsection is None:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return subsection.items()


def getSubsection(xmlCtx, section, subsectionName):
    subsection = section[subsectionName]
    if subsection is None:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return subsection


def readString(xmlCtx, section, subsectionName):
    subsection = section[subsectionName]
    if subsection is None:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return subsection.asString


def readNonEmptyString(xmlCtx, section, subsectionName):
    v = section.readString(subsectionName)
    if not v:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return v


def readBool(xmlCtx, section, subsectionName):
    subsection = section[subsectionName]
    if subsection is None:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return subsection.asBool


def readInt(xmlCtx, section, subsectionName, minVal = None, maxVal = None):
    wrongVal = -123456789
    v = section.readInt(subsectionName, wrongVal)
    if v == wrongVal:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    if minVal is not None and v < minVal or maxVal is not None and v > maxVal:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return v


def readFloat(xmlCtx, section, subsectionName):
    wrongVal = -1000000.0
    v = section.readFloat(subsectionName, wrongVal)
    if v < wrongVal + 1.0:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return v


def readPositiveFloat(xmlCtx, section, subsectionName):
    v = section.readFloat(subsectionName, -1000000.0)
    if v <= 0.0:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return v


def readNonNegativeFloat(xmlCtx, section, subsectionName):
    v = section.readFloat(subsectionName, -1000000.0)
    if v < 0.0:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return v


def readFraction(xmlCtx, section, subsectionName):
    v = section.readFloat(subsectionName, -1000000.0)
    if not 0.0 <= v <= 1.0:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return v


def readVector2(xmlCtx, section, subsectionName):
    wrongVal = (-1000000.0, -1000000.0)
    v = section.readVector2(subsectionName, wrongVal)
    if v[0] < wrongVal[0] + 1.0:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return v


def readPositiveVector2(xmlCtx, section, subsectionName):
    wrongVal = (-1000000.0, -1000000.0)
    v = section.readVector2(subsectionName, wrongVal)
    if v.x <= 0.0 or v.y <= 0.0:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return v


def readVector3(xmlCtx, section, subsectionName):
    wrongVal = (-1000000.0, -1000000.0, -1000000.0)
    v = section.readVector3(subsectionName, wrongVal)
    if v[0] < wrongVal[0] + 1.0:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
    return v


def readTupleOfFloats(xmlCtx, section, subsectionName, count):
    strings = getSubsection(xmlCtx, section, subsectionName).asString.split()
    if len(strings) != count:
        raiseWrongXml(xmlCtx, subsectionName, '%d floats expected' % count)
    try:
        return tuple(map(float, strings))
    except Exception:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)


def readTupleOfInts(xmlCtx, section, subsectionName, count = None):
    strings = getSubsection(xmlCtx, section, subsectionName).asString.split()
    if count is not None and len(strings) != count:
        raiseWrongXml(xmlCtx, subsectionName, '%d ints expected' % count)
    try:
        return tuple(map(int, strings))
    except Exception:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)

    return


def readPrice(xmlCtx, section, subsectionName):
    if section[subsectionName + '/gold'] is not None:
        return (0, readInt(xmlCtx, section, subsectionName, 0))
    else:
        return (readInt(xmlCtx, section, subsectionName, 0), 0)


def readIcon(xmlCtx, section, subsectionName):
    strings = getSubsection(xmlCtx, section, subsectionName).asString.split()
    try:
        return (strings[0], int(strings[1]), int(strings[2]))
    except Exception:
        raiseWrongSection(xmlCtx, subsectionName if subsectionName else section.name)
