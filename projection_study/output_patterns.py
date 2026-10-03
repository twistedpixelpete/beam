"""Pure UV pattern geometry; no Blender or shader dependency."""
# Compact readable 5x7 lettering for projector IDs and native resolution.
FONT = {
'0':['01110','10001','10011','10101','11001','10001','01110'],
'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'5':['11111','10000','10000','11110','00001','00001','11110'],
'6':['01110','10000','10000','11110','10001','10001','01110'],
'7':['11111','00001','00010','00100','01000','01000','01000'],
'8':['01110','10001','10001','01110','10001','10001','01110'],
'9':['01110','10001','10001','01111','00001','00001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'x':['00000','00000','10001','01010','00100','01010','10001'],
' ':['00000']*7,
}

def text_quads(text, centre, height, aspect):
    dy=height/7
    dx=dy*aspect
    left=centre[0]-(len(text)*6-1)*dx/2
    bottom=centre[1]-height/2
    quads=[]
    for index,char in enumerate(text):
        for y,row in enumerate(FONT.get(char,FONT[' '])):
            for x,bit in enumerate(row):
                if bit=='1':
                    u=left+(index*6+x)*dx; v=bottom+(6-y)*dy
                    quads.append(((u,v),(u+dx*.86,v),(u+dx*.86,v+dy*.86),(u,v+dy*.86)))
    return quads


def pattern(mode, identifier, rx, ry, show_grid=True, show_identifier=True):
    lines=[]; quads=[]
    aspect=ry/rx
    nx=16; ny=max(2,round(nx*aspect))
    if mode=='SOLID': quads.append(((0,0),(1,0),(1,1),(0,1)))
    if mode=='CHECKER':
        for x in range(nx):
            for y in range(ny):
                if (x+y)%2==0:
                    quads.append(((x/nx,y/ny),((x+1)/nx,y/ny),((x+1)/nx,(y+1)/ny),(x/nx,(y+1)/ny)))
    if mode=='GRID' and show_grid:
        for i in range(1,nx): lines.append(((i/nx,0),(i/nx,1)))
        for i in range(1,ny): lines.append(((0,i/ny),(1,i/ny)))
        lines += [((0,0),(1,1)),((0,1),(1,0))]
        # Double border, heavy centre cross and corner alignment marks.
        for inset in (0,.006):
            a=inset; b=inset/max(aspect,.01)
            points=[(a,b),(1-a,b),(1-a,1-b),(a,1-b)]
            lines += list(zip(points,points[1:]+points[:1]))
        lines += [((.46,.5),(.54,.5)),((.5,.43),(.5,.57))]
        if show_identifier:
            quads += text_quads(f'{rx} x {ry}',(.5,.09),.055,aspect)
    if show_identifier:
        height=min(.19,.85/(max(1,len(identifier))*6/7*aspect))
        quads += text_quads(identifier,(.5,.68 if mode=='GRID' else .5),height,aspect)
    return lines,quads
