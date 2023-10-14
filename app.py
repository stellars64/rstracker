import pickle
import os
import posixpath
from datetime import datetime
from pathlib import Path

from rs3_api.hiscores import Hiscore
from rs3_api.hiscores.exceptions import UserNotFoundException

from flask import Flask, render_template, request, redirect, url_for

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import CustomJSTickFormatter, HoverTool

from rs3_api.hiscores.exceptions import UserNotFoundException

# ----- Constants -----

# COLOR_PALETTE = {
#     'light': '#f3cba5',
#     'medium': '#975a5e',
#     'dark': '#453953'
# }
COLOR_PALETTE = {
    'light': '#ffffff',
    'medium': '#aaaaaa',
    'dark': '#333333'
}

SKILL_INFO = {
    1:  {'image': "Attack.webp",        'alt': "Attack Icon",        'rs3_api_key': 'attack',         'max_level': 99},
    4:  {'image': "Constitution.webp",  'alt': "Constitution Icon",  'rs3_api_key': 'constitution',   'max_level': 99},
    15: {'image': "Mining.webp",        'alt': "Mining Icon",        'rs3_api_key': 'mining',         'max_level': 99},
    
    3:  {'image': "Strength.webp",      'alt': "Strength Icon",      'rs3_api_key': 'strength',       'max_level': 99},
    17: {'image': "Agility.webp",       'alt': "Agility Icon",       'rs3_api_key': 'agility',        'max_level': 99},
    14: {'image': "Smithing.webp",      'alt': "Smithing Icon",      'rs3_api_key': 'smithing',       'max_level': 99},

    2:  {'image': "Defence.webp",       'alt': "Defence Icon",       'rs3_api_key': 'defence',        'max_level': 99},
    16: {'image': "Herblore.webp",      'alt': "Herblore Icon",      'rs3_api_key': 'herblore',       'max_level': 99},
    11: {'image': "Fishing.webp",       'alt': "Fishing Icon",       'rs3_api_key': 'fishing',        'max_level': 99},

    5:  {'image': "Ranged.webp",        'alt': "Ranged Icon",        'rs3_api_key': 'ranged',         'max_level': 99},
    18: {'image': "Thieving.webp",      'alt': "Thieving Icon",      'rs3_api_key': 'thieving',       'max_level': 99},
    8:  {'image': "Cooking.webp",       'alt': "Cooking Icon",       'rs3_api_key': 'cooking',        'max_level': 99},

    6:  {'image': "Prayer.webp",        'alt': "Prayer Icon",        'rs3_api_key': 'prayer',         'max_level': 99},
    13: {'image': "Crafting.webp",      'alt': "Crafting Icon",      'rs3_api_key': 'crafting',       'max_level': 99},
    12: {'image': "Firemaking.webp",    'alt': "Firemaking Icon",    'rs3_api_key': 'firemaking',     'max_level': 99},

    7:  {'image': "Magic.webp",         'alt': "Magic Icon",         'rs3_api_key': 'magic',          'max_level': 99},
    10: {'image': "Fletching.webp",     'alt': "Fletching Icon",     'rs3_api_key': 'fletching',      'max_level': 99},
    9:  {'image': "Woodcutting.webp",   'alt': "Woodcutting Icon",   'rs3_api_key': 'woodcutting',    'max_level': 99},

    21: {'image': "Runecrafting.webp",  'alt': "Runecrafting Icon",   'rs3_api_key': 'runecrafting',  'max_level': 99},
    19: {'image': "Slayer.webp",        'alt': "Slayer Icon",         'rs3_api_key': 'slayer',        'max_level': 120},
    20: {'image': "Farming.webp",       'alt': "Farming Icon",        'rs3_api_key': 'farming',       'max_level': 120},

    23: {'image': "Construction.webp",  'alt': "Construction Icon",   'rs3_api_key': 'construction',  'max_level': 99},
    22: {'image': "Hunter.webp",        'alt': "Hunter Icon",         'rs3_api_key': 'hunter',        'max_level': 99},
    24: {'image': "Summoning.webp",     'alt': "Summoning Icon",      'rs3_api_key': 'summoning',     'max_level': 99},

    25: {'image': "Dungeoneering.webp", 'alt': "Dungeoneering Icon",  'rs3_api_key': 'dungeoneering', 'max_level': 120},
    26: {'image': "Divination.webp",    'alt': "Divination Icon",     'rs3_api_key': 'divination',    'max_level': 99},
    27: {'image': "Invention.webp",     'alt': "Invention Icon",      'rs3_api_key': 'invention',     'max_level': 120},

    28: {'image': "Archaeology.webp",   'alt': "Archaeology Icon",    'rs3_api_key': 'archeology',    'max_level': 120},
    29: {'image': "Necromancy.png",     'alt': "Necromancy Icon",     'rs3_api_key': 'necromancy',    'max_level': 120},
    0:  {'image': "Overall.webp",       'alt': "Overall Skills Icon", 'rs3_api_key': 'overall',       'max_level': 3018},
}

SKILL_INDEX_OVERALL       = 0
SKILL_INDEX_ATTACK        = 1
SKILL_INDEX_DEFENCE       = 2
SKILL_INDEX_STRENGTH      = 3
SKILL_INDEX_CONSTITUTION  = 4
SKILL_INDEX_RANGED        = 5
SKILL_INDEX_PRAYER        = 6
SKILL_INDEX_MAGIC         = 7
SKILL_INDEX_COOKING       = 8
SKILL_INDEX_WOODCUTTING   = 9
SKILL_INDEX_FLETCHING     = 10
SKILL_INDEX_FISHING       = 11
SKILL_INDEX_FIREMAKING    = 12
SKILL_INDEX_CRAFTING      = 13
SKILL_INDEX_SMITHING      = 14
SKILL_INDEX_MINING        = 15
SKILL_INDEX_HERBLORE      = 16
SKILL_INDEX_AGILITY       = 17
SKILL_INDEX_THIEVING      = 18
SKILL_INDEX_SLAYER        = 19
SKILL_INDEX_FARMING       = 20
SKILL_INDEX_RUNECRAFTING  = 21
SKILL_INDEX_HUNTER        = 22
SKILL_INDEX_CONSTRUCTION  = 23
SKILL_INDEX_SUMMONING     = 24
SKILL_INDEX_DUNGEONEERING = 25
SKILL_INDEX_DIVINATION    = 26
SKILL_INDEX_INVENTION     = 27
SKILL_INDEX_ARCHAEOLOGY   = 28
SKILL_INDEX_NECROMANCY    = 29

SKILL_COLOR_PALETTE = {
    SKILL_INDEX_OVERALL: 
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_ATTACK:
        {'fill': '#8f0a00', 'outline': '#ebc342'},
    SKILL_INDEX_DEFENCE:
        {'fill': '#9cc8d9', 'outline': '#fafafa'},
    SKILL_INDEX_STRENGTH:
        {'fill': '#18910a', 'outline': '#af0a00'},    
    SKILL_INDEX_CONSTITUTION:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_RANGED:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_PRAYER:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_MAGIC:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_COOKING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_WOODCUTTING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_FLETCHING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_FISHING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_FIREMAKING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_CRAFTING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_SMITHING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_MINING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_HERBLORE:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_AGILITY:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_THIEVING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_SLAYER:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_FARMING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_RUNECRAFTING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_HUNTER:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_CONSTRUCTION:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_SUMMONING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_DUNGEONEERING:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_DIVINATION:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_INVENTION:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_ARCHAEOLOGY:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
    SKILL_INDEX_NECROMANCY:
        {'fill': COLOR_PALETTE['light'], 'outline': COLOR_PALETTE['dark']},
}

SKILL_NAMES = [
    "Overall", "Attack", "Defence", "Strength", "Constitution", 
    "Ranged", "Prayer", "Magic", "Cooking", "Woodcutting", "Fletching",
    "Fishing", "Firemaking", "Crafting", "Smithing", "Mining",
    "Herblore", "Agility", "Thieving", "Slayer", "Farming", 
    "Runecrafting", "Hunter", "Construction", "Summoning", 
    "Dungeoneering", "Divination", "Invention", "Archaeology",
    "Necromancy"]

# ----- Class Defs -----

class Session:
    def __init__(self):
        self.username = None
        self.skill = None

'''
    Basically just a wrapper around UserHiscore, that has methods to access data
    using integer codes for skills & stuff
'''
class DataPoint:
    def __init__(self, data):
        self.data = data
        self.timestamp = datetime.now()
    def exp(self, skill):
        return self.data.skills[SKILL_INFO[skill]['rs3_api_key']].experience
    def rank(self, skill):
        return self.data.skills[SKILL_INFO[skill]['rs3_api_key']].rank
    def level(self, skill):
        return self.data.skills[SKILL_INFO[skill]['rs3_api_key']].level
    def username(self):
        return self.data.username
    def account_type(self):
        return self.data.account_type


class PlayerData:
    def __init__(self, username):
        self.USERNAME = username 
        self.DATA_PATH = Path(f'player_data/{self.USERNAME}')
        self.data_points = self._get_cached_data_points()

        current_data = DataPoint(self._get_current_hiscores())
        
        if (not self.data_points) or (self.latest_data().exp(SKILL_INDEX_OVERALL) != current_data.exp(SKILL_INDEX_OVERALL)):
            self.data_points.append(current_data)
            self._cache_data_points()

    def latest_data(self):
        return self.data_points[-1]

    def _get_current_hiscores(self):
        hs = Hiscore().user(self.USERNAME)
        hs.skills = hs.skills[0]
        return hs 

    def _get_cached_data_points(self):
        if not os.path.exists(self.DATA_PATH):
            return []
        else:
            with open(self.DATA_PATH, 'rb+') as f:
                return pickle.load(f)

    def _cache_data_points(self):
        with open(self.DATA_PATH, 'wb+') as f:
            pickle.dump(self.data_points, f)


# ----- Variables -----

app = Flask(__name__)

# ----- Routes -----

@app.route('/')
@app.route('/<name>/<skill>')
@app.route('/<name>/<skill>/<name2>/<skill2>')
def rstracker(name=None, skill=None, name2=None, skill2=None):
    
    newuserdata = []

    userdata = {
        'user1': {},
        'user2': {}
    }

    playerdata1 = None
    playerdata2 = None

    try:
        if name:
            playerdata1 = PlayerData(name)
            userdata['user1'] = {
                'tracked_skill': skill,
                'hiscores': playerdata1.latest_data().data,
                'history': playerdata1
            }
            
            # this is possibly the new form the data will be passed to the web page in
            newuserdata.append({
                'tracked_skill': skill,
                'hiscores': playerdata1.latest_data().data,
                'history': playerdata1
            })

            if name2:
                playerdata2 = PlayerData(name2)
                userdata['user2'] = {
                    'tracked_skill': skill2,
                    'hiscores': playerdata2.latest_data().data,
                    'history': playerdata2
                }

                # this is possibly the new form the data will be passed to the web page in (p2)
                newuserdata.append({
                    'tracked_skill': skill,
                    'hiscores': playerdata2.latest_data().data,
                    'history': playerdata2
                })

    except UserNotFoundException:
        print('user not found?')
        

    # THE ABOVE IS temporary, until I modify create_line_graph to accept the userdata object...
    # graph = create_line_graph(data[0], tracked_skill[0], data[1], tracked_skill[1])

    if userdata['user1']:
        if userdata['user2']:
            graph = create_line_graph(
                    playerdata1, 
                    int(userdata['user1']['tracked_skill']), 
                    playerdata2, 
                    int(userdata['user2']['tracked_skill']))
        else:
            graph = create_line_graph(
                    playerdata1, 
                    int(userdata['user1']['tracked_skill']), 
                    None, None)
    else:
        graph = create_line_graph(None, None, None, None)

    script, div = components(graph)

    print('returning rstracker.html, this page should be found????')
    return render_template(
            'rstracker.html',
            script=script,
            div=div,
            userdata=userdata,
            newuserdata=newuserdata)

# @app.route('/lookup', methods=['POST'])
# def lookup():
#     username = request.form.get('username')
#     skill = request.form.get('skill')
#     print("lookup happened")
#     return redirect(posixpath.join(username, skill))

@app.route('/lookup', methods=['POST'])
def lookup():
    username1 = request.form.get('username1')
    username2 = request.form.get('username2')
    skill1 = request.form.get('skill1')
    skill2 = request.form.get('skill2')
    if username2:
        return redirect(posixpath.join(username1, skill1, username2, skill2))
    else:
        return redirect(posixpath.join(username1, skill1))


@app.route('/lookup2', methods=['POST'])
def lookup2():
    username = request.form.get('username')
    skill = request.form.get('skill')
    username2 = request.form.get('username2')
    skill2 = request.form.get('skill2')
    return redirect(posixpath.join(username, skill, username2, skill2))

@app.template_filter()
def num_to_comma_string(num):
    return format(num, ',')

@app.template_filter()
def max_level(skill):
    return SKILL_INFO[skill]['max_level']

@app.template_filter()
def experience(user_hiscore, skill):
    return user_hiscore.skills[SKILL_INFO[skill]['rs3_api_key']].experience

@app.template_filter()
def level(user_hiscore, skill):
    return user_hiscore.skills[SKILL_INFO[skill]['rs3_api_key']].level

@app.template_filter()
def rank(user_hiscore, skill):
    return user_hiscore.skills[SKILL_INFO[skill]['rs3_api_key']].rank

@app.template_filter()
def skill_icon_url(skill):
    return url_for('static', filename='skillicons/' + SKILL_INFO[skill]['image'])

@app.template_filter()
def skill_alt_text(skill):
    return SKILL_INFO[skill]['alt']

# ----- Bokeh Functions -----

def create_line_graph(player_data, player_skill, player2_data, player2_skill):

    if player_data:
        username = player_data.USERNAME
        skill = player_skill
        timestamps = list(map(lambda e: e.timestamp, player_data.data_points))
        skill_data = list(map(lambda e: e.exp(skill), player_data.data_points))
    else:
        username = ''
        skill = 0
        timestamps = []
        skill_data = []

    if player2_data:
        username2 = player2_data.USERNAME
        skill2 = player2_skill
        timestamps2 = list(map(lambda e: e.timestamp, player2_data.data_points))
        skill2_data = list(map(lambda e: e.exp(skill2), player2_data.data_points))
    else:
        username2 = ''
        skill2 = 0
        timestamps2 = []
        skill2_data = []

    runescape_tick_formatter = CustomJSTickFormatter(
        code = '''
        if (tick < 1000) {
            return tick.toString();
        } else if (tick < 1000000) {
            return (tick / 1000).toString() + 'k';
        } else {
            return (tick / 1000000).toString() + 'm'
        }
        ''')

    if player_data and player2_data:
        plot = figure(
                title=username + '-' + SKILL_NAMES[skill] + ' / ' + username2 + '-' + 
                    SKILL_NAMES[skill2],
                x_axis_label='Time',
                y_axis_label='Exp',
                x_axis_type='datetime',
                sizing_mode='stretch_width',
                max_width=1280,
                background_fill_color=COLOR_PALETTE['medium'],
                border_fill_color=COLOR_PALETTE['dark'],
                outline_line_color=COLOR_PALETTE['medium'])
        skill_line = add_line_to_line_graph(
            plot=plot,
            xvals=timestamps,
            yvals=skill_data,
            #yrange=y_range,
            yrange='default',
            legend_label=SKILL_NAMES[skill],
            color=SKILL_COLOR_PALETTE[skill],
            shape='circle')
        skill2_line = add_line_to_line_graph(
            plot=plot,
            xvals=timestamps2,
            yvals=skill2_data,
            #yrange=y_range,
            yrange='default',
            legend_label=SKILL_NAMES[skill2],
            color=SKILL_COLOR_PALETTE[skill2],
            shape='circle')
        
        skill_hover = HoverTool(
            tooltips=[
                ('Skill', SKILL_NAMES[skill]),
                ('Exp', '@y{0,0}'),
                ('Time', '@x{%m/%d/%Y %H:%M:%S}'),
            ],
            formatters={
                '@x': 'datetime',
                '@y': 'numeral',
            },
            renderers=[skill_line],
            mode='vline',
            anchor='left'
        )
        plot.add_tools(skill_hover)

        skill2_hover = HoverTool(
            tooltips=[
                ('Skill', SKILL_NAMES[skill2]),
                ('Exp', '@y{0,0}'),
                ('Time', '@x{%m/%d/%Y %H:%M:%S}'),
            ],
            formatters={
                '@x': 'datetime',
                '@y': 'numeral',
            },
            renderers=[skill2_line],
            mode='vline',
            anchor='left'
        )
        plot.add_tools(skill2_hover)
    else:
        plot = figure(
                title=username + ' - ' + SKILL_NAMES[skill],
                x_axis_label='Time',
                y_axis_label='Exp',
                x_axis_type='datetime',
                sizing_mode='stretch_width',
                background_fill_color=COLOR_PALETTE['medium'],
                border_fill_color=COLOR_PALETTE['dark'],
                outline_line_color=COLOR_PALETTE['medium'])
        skill_line = add_line_to_line_graph(
            plot=plot,
            xvals=timestamps,
            yvals=skill_data,
            #yrange=y_range,
            yrange='default',
            legend_label=SKILL_NAMES[skill],
            color=SKILL_COLOR_PALETTE[skill],
            shape='circle')
        skill_hover = HoverTool(
            tooltips=[
                ('Skill', SKILL_NAMES[skill]),
                ('Exp', '@y{0,0}'),
                ('Time', '@x{%m/%d/%Y %H:%M:%S}'),
            ],
            formatters={
                '@x': 'datetime',
                '@y': 'numeral',
            },
            renderers=[skill_line],
            mode='vline',
            anchor='left'
        )
        plot.add_tools(skill_hover)


    plot.left[0].formatter = runescape_tick_formatter
    plot.yaxis[0].major_label_text_color = COLOR_PALETTE['light']

    skill_hover.point_policy='snap_to_data'
    skill_hover.line_policy = 'nearest'
    plot.legend.location = 'bottom_right'
    plot.legend.background_fill_color = COLOR_PALETTE['dark']
    plot.legend.title_text_color = COLOR_PALETTE['light']
    plot.legend.label_text_color = COLOR_PALETTE['light']
    plot.legend.border_line_color = COLOR_PALETTE['light']
    plot.xaxis[0].major_label_text_color = COLOR_PALETTE['light']
    plot.xgrid[0].grid_line_alpha = 0.15
    plot.ygrid[0].grid_line_alpha = 0.15
    plot.title.text_color = COLOR_PALETTE['light']

    return plot

def add_line_to_line_graph(plot, xvals, yvals, yrange, legend_label, color, shape):
    line = plot.line(
            xvals,
            yvals,
            y_range_name=yrange,
            legend_label=legend_label,
            line_color=color['fill'],
            line_width=2)
    if shape == 'circle':
        plot.circle(
                xvals, 
                yvals, 
                y_range_name=yrange,
                legend_label=legend_label, 
                line_color=color['outline'],
                fill_color=color['fill'],
                size=8)
    elif shape == 'triangle':
        plot.triangle(
                xvals, 
                yvals, 
                y_range_name=yrange,
                legend_label=legend_label, 
                line_color=color['outline'],
                fill_color=color['fill'],
                size=8)
    return line
    
