import pickle
import os
import posixpath
from datetime import datetime, timedelta
from pathlib import Path

from constants import SKILL

from rs3_api.hiscores import Hiscore
from rs3_api.hiscores.exceptions import UserNotFoundException

from flask import Flask, render_template, request, redirect, url_for

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import CustomJSTickFormatter, HoverTool

from rs3_api.hiscores.exceptions import UserNotFoundException

# ----- Constants -----
COLOR_PALETTE = {
    'light': '#ffffff',
    'medium': '#aaaaaa',
    'dark': '#333333'
}

# ----- Class Defs -----

'''
    Basically just a wrapper around UserHiscore, that has methods to access data
    using integer codes for skills & stuff
'''
class DataPoint:
    def __init__(self, data):
        self.data = data
        self.data.username = self.data.username.lower()
        self.timestamp = datetime.now()
    def exp(self, skill):
        return self.data.skills[SKILL[skill]['rs3_api_key']].experience
    def rank(self, skill):
        return self.data.skills[SKILL[skill]['rs3_api_key']].rank
    def level(self, skill):
        return self.data.skills[SKILL[skill]['rs3_api_key']].level
    def username(self):
        return self.data.username


class PlayerData:
    def __init__(self, username):
        username = username.lower()
        current  = DataPoint(self._get_current_hiscores(username))
        path     = Path(f'player_data/{username}')
        self.data_points = self._get_cached_data_points(path)
        if (not self.data_points) or (self._gained_experience(self.data_points[-1], current)):
            self.data_points.append(current)
            self._cache_data_points(path)
        
    def _gained_experience(self, previous, current):
        return previous.exp(0) != current.exp(0)

    def _get_current_hiscores(self, username):
        hs = Hiscore().user(username)
        hs.skills = hs.skills[0]
        return hs 

    def _get_cached_data_points(self, path):
        if not os.path.exists(path):
            return []
        else:
            with open(path, 'rb+') as f:
                return pickle.load(f)

    def _cache_data_points(self, path):
        with open(path, 'wb+') as f:
            pickle.dump(self.data_points, f)

class Player:
    def __init__(self, index, username, tracked_skill, data_points):
        self.index = index
        self.username = username
        self.tracked_skill = tracked_skill
        self.data_points = data_points   
        self.account_type = self.data_points[-1].data.account_type.value


# ----- Variables -----

app = Flask(__name__)

# ----- Routes -----

@app.route('/')
@app.route('/<timescale>')
@app.route('/<timescale>/<username1>/<skill1>')
@app.route('/<timescale>/<username1>/<skill1>/<username2>/<skill2>')
def rstracker(timescale='last_update', username1=None, skill1=None, username2=None, skill2=None):
    players = []
    try:
        if username1:
            players.append(Player(1, username1.lower(), int(skill1), PlayerData(username1).data_points))
            if username2:
                players.append(Player(2, username2.lower(), int(skill2), PlayerData(username2).data_points))
    except UserNotFoundException:
        print('user not found?')
        
    script, div = components(create_line_graph(players))
    return render_template('rstracker.html', script=script, div=div, players=players, timescale=timescale)

@app.route('/lookup', methods=['POST'])
def lookup():
    timescale = request.form.get('timescale')
    username1 = request.form.get('username1')
    username2 = request.form.get('username2')
    skill1    = request.form.get('skill1')
    skill2    = request.form.get('skill2')
    path      = posixpath.join(timescale) 
    skill1 = '0' if not skill1 else skill1
    skill2 = '0' if not skill2 else skill2
    if username1 and username1 != '':
        path = posixpath.join(path, username1, skill1)
    if username2 and username2 != '':
        path = posixpath.join(path, username2, skill2)
    return redirect(path)

@app.template_filter()
def num_to_comma_string(num):
    return format(num, ',')

@app.template_filter()
def max_level(skill):
    return SKILL[skill]['max_level']

@app.template_filter()
def skill_icon_url(skill):
    return url_for('static', filename='skillicons/' + SKILL[skill]['image'])

@app.template_filter()
def skill_alt_text(skill):
    return SKILL[skill]['alt']

@app.template_filter()
def diff_last_update(player, skill):
    if len(player.data_points) > 1:
        return player.data_points[-1].exp(skill) - player.data_points[-2].exp(skill)
    else:
        return 0

@app.template_filter()
def diff_daily(player, skill):
    today = datetime.now().date()
    for update in player.data_points:
        if update.timestamp.date() == today: 
            return player.data_points[-1].exp(skill) - update.exp(skill)
    return 0

@app.template_filter()
def diff_weekly(player, skill):
    week_ago = datetime.now().date() - timedelta(days=7)
    for update in player.data_points:
        if update.timestamp.date() >= week_ago:
            return player.data_points[-1].exp(skill) - update.exp(skill)
    return 0

# ----- Bokeh Functions -----
def create_line_graph(players):
    
    p1_exists = len(players) > 0
    p2_exists = len(players) > 1
    
    if p1_exists:
        username = players[0].username
        skill = players[0].tracked_skill
        timestamps = list(map(lambda e: e.timestamp, players[0].data_points))
        skill_data = list(map(lambda e: e.exp(skill), players[0].data_points))
    else:
        username = ''
        skill = 0
        timestamps = []
        skill_data = []

    if p2_exists:
        username2 = players[1].username
        skill2 = players[1].tracked_skill
        timestamps2 = list(map(lambda e: e.timestamp, players[1].data_points))
        skill2_data = list(map(lambda e: e.exp(skill2), players[1].data_points))
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

    if p2_exists:
        plot = figure(
                title=username + '-' + SKILL[skill]['name'] + ' / ' + username2 + '-' + 
                    SKILL[skill2]['name'],
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
            legend_label=SKILL[skill]['name'],
            color=SKILL[skill]['colors'],
            shape='circle')
        skill2_line = add_line_to_line_graph(
            plot=plot,
            xvals=timestamps2,
            yvals=skill2_data,
            #yrange=y_range,
            yrange='default',
            legend_label=SKILL[skill2]['name'],
            color=SKILL[skill2]['colors'],
            shape='circle')
        
        skill_hover = HoverTool(
            tooltips=[
                ('Skill', SKILL[skill]['name']),
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
                ('Skill', SKILL[skill2]['name']),
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
                title=username + ' - ' + SKILL[skill]['name'],
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
            legend_label=SKILL[skill]['name'],
            color=SKILL[skill]['colors'],
            shape='circle')
        skill_hover = HoverTool(
            tooltips=[
                ('Skill', SKILL[skill]['name']),
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
    
