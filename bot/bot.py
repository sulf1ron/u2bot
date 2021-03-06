#!/usr/bin python3
# -*- coding:utf-8 -*-

'''
作者: 索尔
邮箱: i@aalyp.cc
UID:  44929
'''

import signal
import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
import random
import math
import requests
import configparser
import time
from jinja2 import Template
from opencc import OpenCC
from api import *
from drive import *

# def
def ismod(id):
	if id in tgconf['admin']:
		return 1
	else:
		return 0

def reply(bot, update, text):
	id = update.effective_user.id
	log(bot, 'reply', id, text)
	update.message.reply_text(text)
	return

def send(bot, update, chat_id, text):
	log(bot, 'send', chat_id, text)
	bot.send_message(chat_id, text)
	return

def log(bot, mode, id, text):
	ts = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
	if id < 0:
#		group = bot.get_chat(id).group
		blog = '(%s, %s) %s(%d): %s' % (ts, mode, '幼兔', id, text)
	else:
		uid = id2uid(id)
		user = bot.get_chat_member(tgconf['group'], id).user
		username = user.username
		blog = '(%s, %s) %s(%d, %d): %s' % (ts, mode, username, id, uid, text)
	print(blog)
	bot_log.write(blog + '\n')
	bot_log.flush()
	return

def start(bot, update):
	send(bot, update, chat_id = update.message.chat_id, text = "请先用 '/set UID' 的格式告诉幼兔娘主人的UID~")
	send(bot, update, chat_id = update.message.chat_id, text = "比如 '/set 44929'")
	return

def new_comer(bot, update, user_data):
	id = update.effective_user.id
	bot.restrict_chat_member(chat_id = tgconf['group'], user_id = id, can_send_messages = False, can_send_media_messages = False, can_send_other_messages = False, can_add_web_page_previews = False)
	send(bot, update, chat_id = update.message.chat_id, text = '主人暂时被禁言了w\n请先按置顶信息告诉幼兔娘主人的UID~\n验证后会自动解禁的哦x')
	return

def set(bot, update, args, user_data):
	id = update.effective_user.id
	cid = update.message.chat_id # chat_id
	uid = int(' '.join(args))
	log(bot, 'set', id, uid)
	if (id2uid(id) != -1) and (confirmed(id)):
		send(bot, update, chat_id = update.message.chat_id, text = '已经知道主人的身份啦，不用重复验证喵')
		return
	real = valid(uid)
	if real == -1:
		send(bot, update, chat_id = cid, text = 'U2娘不理人家了QAQ\n请稍候再试')
		return
	elif not real:
		send(bot, update, chat_id = cid, text = '竟然敢欺骗本兔子, 人家不理你了哼!')
		return
	captcha = init(id, uid)
	status = pm(uid, '验证码', captcha, 'yes')
	if status == -1:
		send(bot, update, chat_id = update.message.chat_id, text = "U2娘不理人家了QAQ\n请稍候使用 '/repm' 再试")
		return
	send(bot, update, chat_id = cid, text = "验证码已经发送给主人了喵，快去U2娘那儿查收w\n请用 '/confirm 验证码' 的格式验明真身~")
	return

def repm(bot, update, user_data):
	id = update.effective_user.id
	log(bot, 'repm', id, '')
	uid = id2uid(id)
	cid = update.message.chat_id # chat_id
	if uid == -1:
		send(bot, update, chat_id = cid, text = '请先告诉幼兔娘主人的UID')
		return
	if confirmed(id):
		send(bot, update, chat_id = update.message.chat_id, text = '已经知道主人的身份啦，不用重复验证喵')
		return
	captcha = str(sql_select('captcha', 'user', 'id', id))
	status = pm(uid, '验证码', captcha, 'yes')
	if status == -1:
		send(bot, update, chat_id = update.message.chat_id, text = "U2娘不理人家了QAQ\n请稍候使用 '/repm' 再试")
		return
	send(bot, update, chat_id = cid, text = '验证码已经发送给主人了喵，快去U2娘那儿查收w')
	return

def confirm(bot, update, args, user_data):
	id = update.effective_user.id
	name = update.effective_user.username
	uid = id2uid(id)
	captcha = ' '.join(args)
	log(bot, 'confirm', id, captcha)
	if uid == -1:
		send(bot, update, chat_id = update.message.chat_id, text = '请先设置UID!')
		return
	if confirmed(id):
		send(bot, update, chat_id = update.message.chat_id, text = '幼兔娘早就认识主人了w')
		return
	real = str(sql_select('captcha', 'user', 'id', id))
	if real == captcha:
		sql_update('user', 'confirmed', 1, 'id', id)
		send(bot, update, chat_id = update.message.chat_id, text = "身份验证成功，幼兔娘记住你啦\n主人自由了！快去愉快地玩耍吧w\n群聊里输入 '幼兔娘 新人礼包' 获取幼兔娘的福利一份~\n悄悄告诉你: 幼兔娘和U2娘的体位很相似的说~ 快去试试吧w")
		bot.restrict_chat_member(chat_id = tgconf['group'], user_id = id, can_send_messages = True, can_send_media_messages = True, can_send_other_messages = True, can_add_web_page_previews = True)
		send(bot, update, chat_id = tgconf['my'], text = '%s: %s' % (name, str(uid)))
	else:
		send(bot, update, chat_id = update.message.chat_id, text = '验证不通过')
		captcha = update_captcha(id)
		status = pm(int(uid), '验证码', captcha, 'yes')
		if status == -1:
			send(bot, update, chat_id = update.message.chat_id, text = "U2娘不理人家了QAQ\n请稍候使用 '/repm' 查收新生成的验证码")
		else:
			send(bot, update, chat_id = update.message.chat_id, text = "请查收新生成的验证码并重试")
	return

def bot_gift(bot, update, uid):
	if newbie(uid):
		status = transfer(uid, 2333, '幼兔娘的新人礼物w, 咱没钱了QAQ')
		if status == 0:
			reply(bot, update, '礼包已发送w')
			old(uid)
		elif status == -1:
			reply(bot, update, 'U2娘不理人家了QAQ')
		elif status == 2:
			reply(bot, update, '请五分钟后再试~')
	else:
		reply(bot, update, '不要贪得无厌哼')
	return

def bot_online(bot, update):
	bot.send_chat_action(tgconf['group'], 'typing')
	if online():
		reply(bot, update, '神经元连结正常')
	else:
		reply(bot, update, 'U2娘不理人家了QAQ')
	return

def bot_uc(bot, update, uid):
	bot.send_chat_action(tgconf['group'], 'typing')
	data = profile(uid)
	if data['code'] == -1:
		reply(bot, update, 'U2娘不理人家了QAQ')
	elif data['code'] == 0:
		reply(bot, update, str(data['uc']['gold']) + '金 ' + str(data['uc']['silver']) + '银 ' + str(data['uc']['copper']) + '铜$_$')
	elif data['code'] == 3:
		reply(bot, update, '你这只傲娇不给幼兔娘看QAQ')
	return

def bot_speed(bot, update, uid):
	bot.send_chat_action(tgconf['group'], 'typing')
	data = speed(uid)
	if data['code'] == -1:
		reply(bot, update, 'U2娘不理人家了QAQ')
		return
	if data['type'] == 0:
		reply(bot, update, '秒收%sUCoin$_$' % (str(data['speed'])))
	else:
		reply(bot, update, '时薪%sUCoin QAQ' % (str(data['speed'])))
	return

def bot_salary(bot, update, uid, type):
	bot.send_chat_action(tgconf['group'], 'typing')
	data = salary(uid, type)
	if data['code'] == -1:
		send(bot, update, chat_id = update.message.chat_id, text = 'U2娘不理人家了QAQ')
		return
	if type == 'h':
		reply(bot, update, '时薪 %s UCoin' % (str(data['uc'])))
	else:
		reply(bot, update, '日薪 %s UCoin' % (str(data['uc'])))
	return

def bot_avatar(bot, update, uid):
	bot.send_chat_action(tgconf['group'], 'upload_photo')
	data = profile(uid)
	if data['code'] == -1:
		reply(bot, update, 'U2娘不理人家了QAQ')
		return
	url = data['avatar']
	if url[0:19] == 'https://u2.dmhy.org':
		photo = get(url)
		if photo == -1:
			reply(bot, update, 'U2娘不理人家了QAQ')
			return
	else:
		try:
			photo = requests.get(url, timeout = 3)
		except:
			reply(bot, update, '头像飞走了~')
			return
	if photo.status_code != 200:
		reply(bot, update, '头像飞走了~')
		return
	open('avatar', 'wb').write(photo.content)
	avatar = open('avatar', 'rb')
	bot.send_photo(chat_id = update.message.chat_id, photo = avatar)
	return

def bot_showup(bot, update, id, uid):
	bot.send_chat_action(tgconf['group'], 'typing')
	last = sql_select('showup_date', 'user', 'id', id)
	now = int(time.time())
	sl = time.localtime(last)
	sn = time.localtime(now)
	if time.strftime("%Y-%m-%d", sl) == time.strftime("%Y-%m-%d", sn):
		reply(bot, update, '今天已经签过到了，请明天再来~')
	else:
		sql_update('user', 'showup_date', now, 'id', id)
		s1 = time.localtime(last + 86400)
		if time.strftime("%Y-%m-%d", s1) == time.strftime("%Y-%m-%d", sn):
			len = sql_select('showup_length', 'user', 'id', id) + 1
		else:
			len = 1
		sql_update('user', 'showup_length', len, 'id', id)
		sweet = random.randint(len * 100 - 50, len * 100)
		transfer(uid, sweet, '每日签到奖励')
		text = '已签到%d天，随机奖励%dUC！' % (len, sweet)
		reply(bot, update, text)
	return

def trick(bot, update, chat_data):
	id = update.effective_user.id
	try:
		text = update.effective_message.text
		if text is not None:
			send(bot, update, chat_id = tgconf['group'], text = text)
	except:
		pass
	try:
		photo_id = update.effective_message.photo[0].file_id
		bot.send_photo(chat_id = tgconf['group'], photo = photo_id)
	except:
		pass
	try:
		sticker_id = update.effective_message.sticker.file_id
		bot.send_sticker(chat_id = tgconf['group'], sticker = sticker_id)
	except:
		pass
	return

def announce(bot, update, chat_data, notify):
	fid = update.message.chat_id
	cid = tgconf['group']
	mid = update.effective_message.message_id
	mid = bot.forward_message(cid, fid, mid).message_id
	if notify:
		bot.pin_chat_message(tgconf['group'], mid)
	else:
		bot.pin_chat_message(tgconf['group'], mid, disable_notification = True)
	return

def bot_chat(bot, update, text, id):
	bot.send_chat_action(tgconf['group'], 'typing')
	word = sm(text, ismod(id))
	if word == -1:
		return
	word = Template(word)
	user = bot.get_chat_member(tgconf['group'], id).user
	data = {}
	data['tg'] = {}
	data['tg']['id'] = user.username
	name = []
	if user.first_name is not None:
		name.append(user.first_name)
	if user.last_name is not None:
		name.append(user.last_name)
	data['tg']['nick'] = ' '.join(name)
	data['u2'] = {}
	data['u2']['uid'] = id2uid(id)
	data['u2']['id'] = uid2id(data['u2']['uid'])
	word = word.render(func = func, data = data)
	reply(bot, update, word)
	return

def bot_sm(bot, update, id, text):
	status = get_sm_status(id)
	if status == 'init':
		num = sm_init(uid)
		update_sm_num(id, num)
		send(bot, update, chat_id = update.message.chat_id, text = '--- %d 号规则 ---' % (num))
		send(bot, update, chat_id = update.message.chat_id, text = "规则名称：")
		return
	elif status == 'name':
		return

def private(bot, update, chat_data, user_data):
	id = update.effective_user.id
	text = update.effective_message.text
	log(bot, 'private', id, text)
	if (text == '幼兔娘 调教') or (select_sm_status(id) != 'init'):
		bot_sm(bot, update, id, text)
		return
	if text == '# trick':
		update_mod_status(id, 'trick')
		return
	elif text == '# !announce':
		update_mod_status(id, '!announce')
		return
	elif text == '# announce':
		update_mod_status(id, 'announce')
		return
	elif text == '# idle':
		update_mod_status(id, 'idle')
		return

	status = mod_status(id)
	if status == 'trick':
		trick(bot, update, chat_data)
#		update_mod_status(id, 'idle')
		return
	elif status == '!announce':
		announce(bot, update, chat_data, 1)
#		update_mod_status(id, 'idle')
		return
	elif status == 'announce':
		announce(bot, update, chat_data, 0)
#		update_mod_status(id, 'idle')
		return

def group(bot, update, chat_data, user_data):
	id = update.effective_user.id
	cid = update.message.chat_id
	text = update.effective_message.text
	text = t2s.convert(text)

#	if (('女' in text) and ('装' in text)) and ((('索' in text) and ('尔' in text)) or (('群' in text) and ('主' in text))):
#		bot.delete_message(update.message.chat_id, update.effective_message.message_id);
#		return
	uid = id2uid(id)
	if text[:3] != '幼兔娘':
		return
	log(bot, 'group', id, text)
	if uid == -1:
		reply(bot, update, '主人请先告诉幼兔娘UID~')
		return
	if not confirmed(id):
		reply(bot, update, '先去验明真身哼')
		return
	text = text[4:]
	if '赚分速度' in text:
		bot_speed(bot, update, uid)
		return
	if ('UC' in text) or ('uc' in text):
		bot_uc(bot, update, uid)
		return
	if '头像' in text:
		bot_avatar(bot, update, uid)
		return
	if '存活' in text:
		bot_online(bot, update)
		return
	if '日薪' in text:
		bot_salary(bot, update, uid, 'd')
		return
	if '时薪' in text:
		bot_salary(bot, update, uid, 'h')
		return
	if ('糖' in text) or ('新人礼包' in text):
		bot_gift(bot, update, uid)
		return
	if ('签到' in text) or ('打卡' in text):
		bot_showup(bot, update, id, uid)
		return
	bot_chat(bot, update, text, id)
	return

# 初始化
signal.signal(signal.SIGINT, dbexit)
signal.signal(signal.SIGTERM, dbexit)

bot_log = open('bot.log', 'a')

t2s = OpenCC('t2s')

conf = configparser.ConfigParser()
conf.read('secret.ini')

tgconf = {}
tgconf['token'] = conf.get('TG', 'token')

bot = telegram.Bot(token = tgconf['token'])
print(bot.get_me())
updater = Updater(token = tgconf['token'])
dispatcher = updater.dispatcher

tgconf['my'] = int(conf.get('TG', 'my'))
tgconf['group'] = int(conf.get('TG', 'group'))
tgconf['admin'] = [member.user.id for member in bot.get_chat_administrators(tgconf['group'])]

print(tgconf['admin'])

func = conf.get('PY', 'func')
funcn = eval(func)
funcm = eval(func.replace('\'', ''))
func = dict(zip(funcn, funcm))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = 200)

# Handler
private_handler = MessageHandler((Filters.private & (~ Filters.command)), private, pass_chat_data = True, pass_user_data = True)
group_handler = MessageHandler(Filters.text, group, pass_chat_data = True, pass_user_data = True, edited_updates = True)
new_comer_handler = MessageHandler(Filters.status_update.new_chat_members, new_comer, pass_user_data = True)
start_handler = CommandHandler('start', start)
set_handler = CommandHandler('set', set, pass_args = True, pass_user_data = True)
repm_handler = CommandHandler('repm', repm, pass_user_data = True)
confirm_handler = CommandHandler('confirm', confirm, pass_args = True, pass_user_data = True)

dispatcher.add_handler(private_handler)
dispatcher.add_handler(group_handler)
dispatcher.add_handler(new_comer_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(set_handler)
dispatcher.add_handler(repm_handler)
dispatcher.add_handler(confirm_handler)

if __name__ == '__main__':
	updater.start_polling()
