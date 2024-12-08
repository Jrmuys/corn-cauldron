from PIL import Image, ImageDraw, ImageFont
import requests
import math

font = "assets/fonts/inter_variable.ttf"

lane_outcomes = [
'TIE',
'RADIANT_VICTORY',
'RADIANT_STOMP',
'DIRE_VICTORY',
'DIRE_STOMP',
]

font_size_cache = {}

def get_font(size):
    if size not in font_size_cache:
        font_size_cache[size] = ImageFont.truetype(font, size)
    return font_size_cache[size]

def get_text_size(text, font):
    bbox = font.getbbox(text)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1], bbox[1])
    
def get_image_from_url(url):
    return Image.open(requests.get(url, stream=True).raw)

def number_shortener(number):
    if number >= 1000000:
        return f'{int(round(number / 1000000, 1))}M'
    if number >= 1000:
        return f'{int(round(number / 1000, 1))}K'
    return str(number)

    

class Table:
    def __init__(self, title):
        self.rows = []
        self.title = title
        self.min_row_height = 20
        
        

    def add_row(self, row):
        self.rows.append(row)

    def draw(self):
        print('Drawing table')
        
        title_font = get_font(24)
        title_size = get_text_size(self.title, title_font)
        
        rowHeights = [self.min_row_height] * len(self.rows)
        for i, row in enumerate(self.rows):
            for cell in row:
                rowHeights[i] = max(rowHeights[i], cell.height)
        
        if self.rows:
            columnWidths = [0] * len(self.rows[0])
        else:
            columnWidths = []
        
        for row in self.rows:
            for i, cell in enumerate(row):
                columnWidths[i] = max(columnWidths[i], cell.width)
        
        totalWidth = sum(columnWidths)
        totalHeight = title_size[1] + sum(rowHeights)
        
        print('Total width:', totalWidth)
        print('Total height:', totalHeight)
        
        image = Image.new('RGB', (totalWidth, totalHeight), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        draw.text((0, -title_size[2]), self.title, font=title_font, spacing=0, fill=(0, 0, 0))
        # Draw a red border around the title
        draw.rectangle([0, 0, title_size[0], title_size[1]], outline=(255, 0, 0))
        text_bbox = draw.textbbox((0, 0), self.title, font=title_font)
        draw.rectangle(text_bbox, outline=(0, 255, 0))
        y = title_size[1]
        for i, row in enumerate(self.rows):
            x = 0
            for j, cell in enumerate(row):
                image, draw = cell.draw(draw, image, x, y, columnWidths[j], rowHeights[i])
                x += columnWidths[j]
            y += rowHeights[i]
                
        return image
            
        
class Cell:
    def __init__(self, **kwargs):
        self.width = kwargs.get('width', 0)
        self.height = kwargs.get('height', 0)
        
    def draw(self, draw, image, x, y, width, height):
        print('Drawing cell with width', self.width, 'and height', self.height)
        
        return image, draw
        
class HeaderCell(Cell):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = kwargs.get('font_size', 12)
        self.font = get_font(self.font_size)
        self.text_size = get_text_size(self.text, self.font)
        self.padding = kwargs.get('padding', [0, 8, 0, 8])
        
        if not self.width:
            self.width = self.padding[1] + self.padding[3] + self.text_size[0]
        if not self.height:
            self.height = self.padding[0] + self.padding[2] + self.text_size[1]
            
        
    def draw(self, draw, image, x, y, width, height):
        print('Drawing header cell with text:', self.text)
        # Draw the text in the center of the cell
        # text_x = x + (width - self.text_size[0]) // 2
        # text_y = y + (height - self.text_size[1]) // 2
        
        text_x = int(x + (width / 2) - (self.text_size[0] / 2))
        text_y = int(y + (height / 2) - (self.text_size[1] / 2))

        print(f'x: {x}, y: {y}, width: {width}, height: {height}')        
        print(f'text_size: {self.text_size}, text_x: {text_x}, text_y: {text_y}')
        print(f'relative text_x: {text_x - x}, relative text_y: {text_y - y}, text size: {self.text_size}')
        
        
        
        # Add background color
        draw.rectangle([x, y, x + width, y + height], fill=(200, 200, 200)) 
        #Draw red outline around text bbox
        # draw.rectangle([text_x, text_y, text_x + self.text_size[0], text_y + self.text_size[1]], outline=(255, 0, 0))
        
        draw.text((text_x, text_y-self.text_size[2]), self.text, font=self.font, fill=(0, 0, 0))
        
        return image, draw

        
class TextCell(Cell):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.justify = kwargs.get('justify', 'left')
        self.padding = kwargs.get('padding', [0, 6, 0, 6])
        self.font_size = kwargs.get('font_size', 12)
        self.font = get_font(self.font_size)
        
        
        self.text_size = get_text_size(self.text, self.font)
        if not self.width:
            self.width = self.padding[1] + self.padding[3] + self.text_size[0]
        if not self.height:
            self.height = self.padding[0] + self.padding[2] + self.text_size[1]
        
    def draw(self, draw, image, x, y, width, height):
        print('Drawing text cell with text:', self.text)
        
        text_x = int(x + (width / 2) - (self.text_size[0] / 2))
        text_y = int(y + (height / 2) - (self.text_size[1] / 2))
        
        draw.text((text_x, text_y-self.text_size[2]), self.text, font=self.font, fill=(0, 0, 0))
        return image, draw

        
class HeroImageCell(Cell):
    def __init__(self, image, **kwargs):
        super().__init__(**kwargs)
        self.image = image
        self.image_height = image.height
        self.image_width = image.width
        self.height = kwargs.get('height', 30)
        
    def draw(self, draw, image, x, y, width, height):
        print('Drawing image cell with image:', self.image)
        # Draw the image in the center of the cell, maintaining aspect ratio
        aspect_ratio = self.image_width / self.image_height
        self.image = self.image.resize((int(height * aspect_ratio), height))
        self.image = self.image.crop((0, 0, width, height))
        image.paste(self.image, (x, y))
        
        
        return image, draw

        
class ItemCell(Cell):
    def __init__(self, item_name, **kwargs):
        super().__init__(**kwargs)
        self.item_images = []
        
    def draw(self, draw, image, x, y, width, height):
        print('Drawing item cell')
        
        return image, draw

class NeutralItemCell(Cell):
    def __init__(self, item_name, **kwargs):
        super().__init__(**kwargs)
        self.item_image = None
        
    def draw(self, draw, image, x, y, width, height):
        print('Drawing neutral item cell')
        
        return image, draw
        
class LaneOutcomeCell(Cell):
    def __init__(self, outcome, **kwargs):
        super().__init__(**kwargs)
        self.outcome = outcome
        self.width = 60
        
    def draw(self, draw, image, x, y, width, height):
        print('Drawing lane outcome cell with outcome:', self.outcome)
        
        text_x = int(x + (width / 2) - 6)
        text_y = int(y + (height / 2) - 6)
        
        # Calculate text position
        font = get_font(12)
        ascent, descent = font.getmetrics()
        text_height = ascent + descent
        
        if (lane_outcomes[self.outcome] == 'TIE'):
            text = 'TIE'
        elif (lane_outcomes[self.outcome] == 'RADIANT_VICTORY'):
            text = 'RW'
        elif (lane_outcomes[self.outcome] == 'RADIANT_STOMP'):
            text = 'RS'
        elif (lane_outcomes[self.outcome] == 'DIRE_VICTORY'):
            text = 'DW'
        elif (lane_outcomes[self.outcome] == 'DIRE_STOMP'):
            text = 'DS'
        else:
            text = ''
        
        text_width = get_text_size(text, font)[0] 
        text_x = x + (width - text_width) // 2
        text_y = y + (height - text_height) // 2
        
        draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))
        return image, draw

if __name__ == '__main__':
    # Output test table image
    table = Table('Match 10239581')
    table.add_row([
        HeaderCell('Player'),
        HeaderCell('Hero'),
        HeaderCell('Kills'),
        HeaderCell('Deaths'),
        HeaderCell('Assists'),
        HeaderCell('Networth'),
        HeaderCell('Role'),
        HeaderCell('Lane'),
        HeaderCell('Items'),
        HeaderCell('Neutral Item')
    ])
    hero_image = get_image_from_url('https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/kez.png?')
    table.add_row([
        TextCell('Player Long Name'),
        HeroImageCell(hero_image),
        TextCell('10'),
        TextCell('2'),
        TextCell('5'),
        TextCell(number_shortener(10000)),
        TextCell('Carry'),
        LaneOutcomeCell(1),
        ItemCell('item1'),
        NeutralItemCell('neutral item')
    ])
    
    image = table.draw()
    
    image.show()
    image.save('table.png')
    
    
    # Example usage
    