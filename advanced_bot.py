#!/usr/bin/env python3
"""
LangSense Bot - نظام متكامل متقدم
إدارة شاملة للمستخدمين والمعاملات ووسائل الدفع
"""

import os
import json
import time
import logging
import csv
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedLangSenseBot:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.user_states = {}  # لحفظ حالات المستخدمين
        self.init_files()
        self.admin_ids = self.get_admin_ids()  # جلب معرفات الأدمن
        
    def init_files(self):
        """إنشاء جميع ملفات النظام"""
        # ملف المستخدمين
        if not os.path.exists('users.csv'):
            with open('users.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['telegram_id', 'name', 'phone', 'customer_id', 'language', 'date', 'is_banned', 'ban_reason'])
        
        # ملف المعاملات المتقدم
        if not os.path.exists('transactions.csv'):
            with open('transactions.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'customer_id', 'telegram_id', 'name', 'type', 'amount', 'status', 'date', 'admin_note', 'payment_method', 'receipt_info', 'processed_by'])
        
        # ملف وسائل الدفع
        if not os.path.exists('payment_methods.csv'):
            with open('payment_methods.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'name', 'type', 'details', 'is_active', 'created_date'])
                # وسائل افتراضية
                default_methods = [
                    ['1', 'البنك الأهلي', 'deposit', 'رقم الحساب: 1234567890\nاسم المستفيد: شركة النظام المالي', 'active'],
                    ['2', 'بنك الراجحي', 'deposit', 'رقم الحساب: 0987654321\nاسم المستفيد: شركة النظام المالي', 'active'],  
                    ['3', 'STC Pay', 'withdraw', 'رقم الجوال: 0501234567', 'active'],
                    ['4', 'مدى البنك الأهلي', 'withdraw', 'رقم الحساب: 1111222233334444', 'active']
                ]
                for method in default_methods:
                    writer.writerow(method + [datetime.now().strftime('%Y-%m-%d')])
        
        logger.info("تم إنشاء جميع ملفات النظام بنجاح")
        
    def api_call(self, method, data=None):
        """استدعاء API مُحسن"""
        url = f"{self.api_url}/{method}"
        try:
            if data:
                json_data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=json_data)
                req.add_header('Content-Type', 'application/json')
            else:
                req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
                
        except Exception as e:
            logger.error(f"خطأ في API: {e}")
            return None
    
    def send_message(self, chat_id, text, keyboard=None):
        """إرسال رسالة"""
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        if keyboard:
            data['reply_markup'] = keyboard
        return self.api_call('sendMessage', data)
    
    def get_updates(self):
        """جلب التحديثات"""
        url = f"{self.api_url}/getUpdates?offset={self.offset + 1}&timeout=10"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"خطأ في جلب التحديثات: {e}")
            return None
    
    def get_admin_ids(self):
        """جلب معرفات الأدمن"""
        admin_ids = os.getenv('ADMIN_USER_IDS', '').split(',')
        return [admin_id.strip() for admin_id in admin_ids if admin_id.strip()]
    
    def is_admin(self, telegram_id):
        """فحص صلاحية الأدمن"""
        return str(telegram_id) in self.admin_ids
    
    def notify_admins(self, message):
        """إشعار فوري لجميع الأدمن"""
        for admin_id in self.admin_ids:
            try:
                self.send_message(admin_id, message)
            except:
                pass
    
    def is_user_banned(self, telegram_id):
        """فحص حظر المستخدم"""
        user = self.find_user(telegram_id)
        return user and user.get('is_banned', 'no') == 'yes'
    
    def find_user(self, telegram_id):
        """البحث عن مستخدم"""
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['telegram_id'] == str(telegram_id):
                        return row
        except:
            pass
        return None
    
    def search_users(self, query):
        """البحث في المستخدمين"""
        results = []
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (query.lower() in row['name'].lower() or 
                        query in row['customer_id'] or 
                        query in row['phone']):
                        results.append(row)
        except:
            pass
        return results
    
    def get_payment_methods(self, method_type=None):
        """جلب وسائل الدفع"""
        methods = []
        try:
            with open('payment_methods.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if method_type is None or row['type'] == method_type:
                        if row['is_active'] == 'active':
                            methods.append(row)
        except:
            pass
        return methods
    
    def get_pending_transactions(self):
        """جلب المعاملات المعلقة"""
        pending = []
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['status'] == 'pending':
                        pending.append(row)
        except:
            pass
        return pending
    
    def update_transaction_status(self, trans_id, new_status, admin_note='', admin_id=''):
        """تحديث حالة المعاملة"""
        transactions = []
        try:
            # قراءة جميع المعاملات
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['id'] == trans_id:
                        row['status'] = new_status
                        if admin_note:
                            row['admin_note'] = admin_note
                        row['processed_by'] = admin_id
                    transactions.append(row)
            
            # إعادة كتابة الملف
            with open('transactions.csv', 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['id', 'customer_id', 'telegram_id', 'name', 'type', 'amount', 'status', 'date', 'admin_note', 'payment_method', 'receipt_info', 'processed_by']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(transactions)
            return True
        except:
            return False
    
    def ban_user(self, customer_id, reason, admin_id):
        """حظر مستخدم"""
        users = []
        success = False
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['customer_id'] == customer_id:
                        row['is_banned'] = 'yes'
                        row['ban_reason'] = reason
                        success = True
                    users.append(row)
            
            if success:
                with open('users.csv', 'w', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['telegram_id', 'name', 'phone', 'customer_id', 'language', 'date', 'is_banned', 'ban_reason']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(users)
        except:
            pass
        return success
    
    def main_keyboard(self, lang='ar'):
        """القائمة الرئيسية"""
        if lang == 'ar':
            return {
                'keyboard': [
                    [{'text': '💰 طلب إيداع'}, {'text': '💸 طلب سحب'}],
                    [{'text': '📋 طلباتي'}, {'text': '👤 حسابي'}],
                    [{'text': '📨 شكوى'}, {'text': '🆘 دعم'}],
                    [{'text': '🇺🇸 English'}, {'text': '/admin'}]
                ],
                'resize_keyboard': True
            }
        else:
            return {
                'keyboard': [
                    [{'text': '💰 Deposit Request'}, {'text': '💸 Withdrawal Request'}],
                    [{'text': '📋 My Requests'}, {'text': '👤 Profile'}],
                    [{'text': '📨 Complaint'}, {'text': '🆘 Support'}],
                    [{'text': '🇸🇦 العربية'}, {'text': '/admin'}]
                ],
                'resize_keyboard': True
            }
    
    def create_deposit_request(self, message):
        """إنشاء طلب إيداع متقدم"""
        user = self.find_user(message['from']['id'])
        if not user:
            return
        
        # عرض وسائل الإيداع المتاحة
        deposit_methods = self.get_payment_methods('deposit')
        if not deposit_methods:
            self.send_message(message['chat']['id'], "❌ لا توجد وسائل إيداع متاحة حالياً")
            return
        
        methods_text = "💰 طلب إيداع جديد\n\nوسائل الإيداع المتاحة:\n\n"
        keyboard_buttons = []
        
        for method in deposit_methods:
            methods_text += f"🏦 {method['name']}\n{method['details']}\n\n"
            keyboard_buttons.append([{'text': f"💳 {method['name']}"}])
        
        keyboard_buttons.append([{'text': '🔙 العودة للقائمة الرئيسية'}])
        
        methods_text += "اختر وسيلة الإيداع المناسبة:"
        
        self.send_message(message['chat']['id'], methods_text, {
            'keyboard': keyboard_buttons,
            'resize_keyboard': True,
            'one_time_keyboard': True
        })
        
        # حفظ حالة المستخدم
        self.user_states[message['from']['id']] = 'selecting_deposit_method'
    
    def process_deposit_method_selection(self, message):
        """معالجة اختيار وسيلة الإيداع"""
        user = self.find_user(message['from']['id'])
        selected_method = message['text'].replace('💳 ', '')
        
        # البحث عن الوسيلة المختارة
        deposit_methods = self.get_payment_methods('deposit')
        selected_method_info = None
        for method in deposit_methods:
            if method['name'] == selected_method:
                selected_method_info = method
                break
        
        if not selected_method_info:
            self.send_message(message['chat']['id'], "❌ وسيلة الدفع غير صحيحة")
            return
        
        # إنشاء المعاملة
        trans_id = f"DEP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        response = f"""✅ تم اختيار وسيلة الإيداع: {selected_method}

🆔 رقم المعاملة: {trans_id}
📱 العميل: {user['name']} ({user['customer_id']})
🏦 وسيلة الدفع: {selected_method}

📋 تفاصيل التحويل:
{selected_method_info['details']}

📝 لإتمام الطلب، يرجى إرسال:
1️⃣ المبلغ المراد إيداعه (رقم فقط)
2️⃣ صورة إيصال التحويل

مثال: 1000"""
        
        # حفظ المعاملة
        with open('transactions.csv', 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                trans_id, user['customer_id'], user['telegram_id'], user['name'], 
                'deposit', '0', 'pending', datetime.now().strftime('%Y-%m-%d %H:%M'), 
                '', selected_method, 'awaiting_details', ''
            ])
        
        # إشعار فوري شامل للأدمن
        admin_notification = f"""🚨 طلب إيداع جديد - مرحلة 1

🆔 رقم المعاملة: {trans_id}
👤 العميل: {user['name']} ({user['customer_id']})
📱 تيليجرام: @{message['from'].get('username', 'غير متوفر')} ({user['telegram_id']})
📞 الهاتف: {user['phone']}
🏦 وسيلة الدفع المختارة: {selected_method}
📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}
🔢 المرحلة: انتظار إدخال المبلغ

📋 تفاصيل وسيلة الدفع:
{selected_method_info['details']}

⏳ العميل الآن يدخل المبلغ المطلوب..."""
        
        self.notify_admins(admin_notification)
        
        self.send_message(message['chat']['id'], response)
        self.user_states[message['from']['id']] = f'deposit_amount_{trans_id}'
    
    def handle_admin_search(self, message):
        """البحث في المستخدمين للأدمن"""
        if not self.is_admin(message['from']['id']):
            return
        
        parts = message['text'].split(' ', 1)
        if len(parts) < 2:
            self.send_message(message['chat']['id'], "استخدم: /search اسم_أو_رقم_العميل")
            return
        
        query = parts[1]
        results = self.search_users(query)
        
        if not results:
            self.send_message(message['chat']['id'], f"❌ لم يتم العثور على نتائج للبحث: {query}")
            return
        
        response = f"🔍 نتائج البحث عن: {query}\n\n"
        for user in results:
            ban_status = "🚫 محظور" if user.get('is_banned') == 'yes' else "✅ نشط"
            response += f"👤 {user['name']}\n🆔 {user['customer_id']}\n📱 {user['phone']}\n🔸 {ban_status}\n\n"
        
        self.send_message(message['chat']['id'], response)
    
    def handle_admin_ban(self, message):
        """حظر مستخدم"""
        if not self.is_admin(message['from']['id']):
            return
        
        parts = message['text'].split(' ', 2)
        if len(parts) < 3:
            self.send_message(message['chat']['id'], "استخدم: /ban رقم_العميل سبب_الحظر")
            return
        
        customer_id = parts[1]
        reason = parts[2]
        
        if self.ban_user(customer_id, reason, str(message['from']['id'])):
            # إشعار المستخدم بالحظر
            user = None
            try:
                with open('users.csv', 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['customer_id'] == customer_id:
                            user = row
                            break
            except:
                pass
            
            if user:
                self.send_message(user['telegram_id'], f"🚫 تم حظر حسابك\n\nالسبب: {reason}\n\nللاستفسار تواصل مع الإدارة")
            
            self.send_message(message['chat']['id'], f"✅ تم حظر العميل {customer_id} بنجاح")
        else:
            self.send_message(message['chat']['id'], f"❌ فشل في حظر العميل {customer_id}")
    
    def handle_admin_pending(self, message):
        """عرض الطلبات المعلقة"""
        if not self.is_admin(message['from']['id']):
            return
        
        pending = self.get_pending_transactions()
        if not pending:
            self.send_message(message['chat']['id'], "✅ لا توجد طلبات معلقة")
            return
        
        response = f"⏳ الطلبات المعلقة ({len(pending)}):\n\n"
        for trans in pending:
            response += f"🆔 {trans['id']}\n👤 {trans['name']} ({trans['customer_id']})\n💰 {trans['type']}: {trans['amount']} ريال\n📅 {trans['date']}\n\n"
        
        response += "\n💡 للموافقة: /approve رقم_المعاملة\n💡 للرفض: /reject رقم_المعاملة سبب"
        
        self.send_message(message['chat']['id'], response)
    
    def handle_text(self, message):
        """معالجة الرسائل النصية الرئيسية"""
        if self.is_user_banned(message['from']['id']):
            self.send_message(message['chat']['id'], "🚫 حسابك محظور. تواصل مع الإدارة للاستفسار.")
            return
        
        text = message['text']
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        
        # فحص الأوامر الإدارية
        if self.is_admin(user_id):
            if text.startswith('/search '):
                self.handle_admin_search(message)
                return
            elif text.startswith('/ban '):
                self.handle_admin_ban(message)
                return
            elif text == '/pending':
                self.handle_admin_pending(message)
                return
            elif text.startswith('/approve '):
                self.handle_admin_approve(message)
                return
            elif text.startswith('/reject '):
                self.handle_admin_reject(message)
                return
            # معالجة أزرار الأدمن
            elif text == '📋 الطلبات المعلقة':
                self.handle_admin_pending(message)
                return
            elif text == '✅ طلبات مُوافقة':
                self.show_approved_transactions(message)
                return
            elif text == '👥 إدارة المستخدمين':
                self.show_users_management(message)
                return
            elif text == '🔍 البحث':
                self.prompt_admin_search(message)
                return
            elif text == '💳 وسائل الدفع':
                self.show_payment_methods_admin(message)
                return
            elif text == '📊 الإحصائيات':
                self.show_detailed_stats(message)
                return
            elif text == '📢 إرسال جماعي':
                self.prompt_broadcast(message)
                return
            elif text == '🚫 حظر مستخدم':
                self.prompt_ban_user(message)
                return
            elif text == '✅ إلغاء حظر':
                self.prompt_unban_user(message)
                return
            elif text == '📝 إضافة وسيلة دفع':
                self.prompt_add_payment_method(message)
                return
            elif text == '⚙️ تعديل وسائل الدفع':
                self.show_edit_payment_methods(message)
                return
            elif text == '🏠 القائمة الرئيسية':
                user = self.find_user(user_id)
                lang = user.get('language', 'ar') if user else 'ar'
                welcome_text = f"مرحباً! 👋\nتم العودة للقائمة الرئيسية"
                self.send_message(chat_id, welcome_text, self.main_keyboard(lang))
                return
        
        # فحص حالات المستخدم
        if user_id in self.user_states:
            state = self.user_states[user_id]
            if state == 'selecting_deposit_method':
                self.process_deposit_method_selection(message)
                return
            elif state.startswith('deposit_amount_'):
                self.process_deposit_amount(message)
                return
            elif state == 'admin_searching':
                self.process_admin_search(message)
                return
            elif state == 'admin_broadcasting':
                self.process_admin_broadcast(message)
                return
            elif state == 'admin_banning':
                self.process_admin_ban(message)
                return
            elif state == 'admin_unbanning':
                self.process_admin_unban(message)
                return
            elif state == 'selecting_withdraw_method':
                self.process_withdrawal_method_selection(message)
                return
            elif state.startswith('withdraw_wallet_'):
                self.process_withdrawal_wallet(message)
                return
            elif state.startswith('withdraw_amount_'):
                self.process_withdrawal_amount(message)
                return
            elif state == 'admin_adding_payment':
                self.process_admin_add_payment(message)
                return
            elif state == 'admin_editing_payment':
                self.process_admin_edit_payment(message)
                return
        
        user = self.find_user(user_id)
        if not user:
            self.handle_start(message)
            return
        
        lang = user.get('language', 'ar')
        
        # معالجة القوائم
        if text in ['💰 طلب إيداع', '💰 Deposit Request']:
            self.create_deposit_request(message)
        elif text in ['💸 طلب سحب', '💸 Withdrawal Request']:
            self.create_withdrawal_request(message)
        elif text in ['📋 طلباتي', '📋 My Requests']:
            self.show_user_transactions(message)
        elif text == '/admin' and self.is_admin(user_id):
            self.handle_admin_panel(message)
        else:
            self.send_message(chat_id, "اختر من القائمة:", self.main_keyboard(lang))
    
    def show_user_transactions(self, message):
        """عرض طلبات المستخدم"""
        user = self.find_user(message['from']['id'])
        if not user:
            return
        
        transactions = []
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['customer_id'] == user['customer_id']:
                        transactions.append(row)
        except:
            pass
        
        if not transactions:
            self.send_message(message['chat']['id'], "📋 لا توجد طلبات سابقة")
            return
        
        response = f"📋 طلباتك ({len(transactions)}):\n\n"
        for trans in transactions[-10:]:  # آخر 10 طلبات
            status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(trans['status'], "❓")
            response += f"{status_emoji} {trans['id']}\n💰 {trans['type']}: {trans['amount']} ريال\n📅 {trans['date']}\n"
            if trans.get('admin_note'):
                response += f"📝 ملاحظة: {trans['admin_note']}\n"
            response += "\n"
        
        self.send_message(message['chat']['id'], response)
    
    def get_transaction_info(self, trans_id):
        """جلب معلومات معاملة"""
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['id'] == trans_id:
                        return row
        except:
            pass
        return None
    
    def handle_admin_approve(self, message):
        """موافقة الأدمن على طلب مع إشعار فوري"""
        if not self.is_admin(message['from']['id']):
            return
        
        parts = message['text'].split(' ', 1)
        if len(parts) < 2:
            return
        
        trans_id = parts[1]
        admin_name = message['from'].get('first_name', 'الإدارة')
        
        if self.update_transaction_status(trans_id, 'approved', f'تمت الموافقة من {admin_name}', str(message['from']['id'])):
            # إشعار فوري للمستخدم مع تفاصيل كاملة
            trans_info = self.get_transaction_info(trans_id)
            if trans_info:
                user_notification = f"""🎉 تمت الموافقة على طلبك!

🆔 رقم المعاملة: {trans_id}
💰 النوع: {trans_info['type']}
💵 المبلغ: {trans_info['amount']} ريال
⏰ وقت الموافقة: {datetime.now().strftime('%Y-%m-%d %H:%M')}
👤 معالج بواسطة: {admin_name}

✅ تم معالجة طلبك بنجاح
شكراً لاستخدام خدماتنا"""
                
                try:
                    self.send_message(trans_info['telegram_id'], user_notification)
                except:
                    pass
            
            admin_response = f"✅ تمت الموافقة على الطلب {trans_id}\n📱 تم إشعار العميل فوراً"
            self.send_message(message['chat']['id'], admin_response, self.admin_keyboard())
        else:
            self.send_message(message['chat']['id'], f"❌ فشل في الموافقة على الطلب {trans_id}", self.admin_keyboard())
    
    def handle_admin_reject(self, message):
        """رفض طلب مع إشعار فوري محسن"""
        if not self.is_admin(message['from']['id']):
            return
        
        parts = message['text'].split(' ', 2)
        if len(parts) < 3:
            self.send_message(message['chat']['id'], "استخدم: /reject رقم_المعاملة السبب", self.admin_keyboard())
            return
        
        trans_id = parts[1]
        reason = parts[2]
        admin_name = message['from'].get('first_name', 'الإدارة')
        
        if self.update_transaction_status(trans_id, 'rejected', f'مرفوض: {reason}', str(message['from']['id'])):
            trans_info = self.get_transaction_info(trans_id)
            if trans_info:
                user_notification = f"""❌ تم رفض طلبك

🆔 رقم المعاملة: {trans_id}
💰 النوع: {trans_info['type']}
💵 المبلغ: {trans_info['amount']} ريال
⏰ وقت الرفض: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📝 سبب الرفض: {reason}

💡 يمكنك إنشاء طلب جديد إذا أردت
للاستفسار تواصل مع الإدارة"""
                
                try:
                    self.send_message(trans_info['telegram_id'], user_notification)
                except:
                    pass
            
            admin_response = f"✅ تم رفض الطلب {trans_id}\n📱 تم إشعار العميل بالسبب فوراً"
            self.send_message(message['chat']['id'], admin_response, self.admin_keyboard())
        else:
            self.send_message(message['chat']['id'], f"❌ فشل في رفض الطلب {trans_id}", self.admin_keyboard())
    
    def admin_keyboard(self):
        """لوحة أزرار الأدمن الشاملة"""
        return {
            'keyboard': [
                [{'text': '📋 الطلبات المعلقة'}, {'text': '✅ طلبات مُوافقة'}],
                [{'text': '👥 إدارة المستخدمين'}, {'text': '🔍 البحث'}],
                [{'text': '💳 وسائل الدفع'}, {'text': '📊 الإحصائيات'}],
                [{'text': '📢 إرسال جماعي'}, {'text': '🔧 إعدادات'}],
                [{'text': '🚫 حظر مستخدم'}, {'text': '✅ إلغاء حظر'}],
                [{'text': '📝 إضافة وسيلة دفع'}, {'text': '⚙️ تعديل وسائل الدفع'}],
                [{'text': '🏠 القائمة الرئيسية'}]
            ],
            'resize_keyboard': True
        }
    
    def handle_admin_panel(self, message):
        """لوحة إدارة شاملة بالأزرار"""
        if not self.is_admin(message['from']['id']):
            return
        
        # إحصائيات شاملة
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                users = list(csv.DictReader(f))
                total_users = len(users)
                banned_users = len([u for u in users if u.get('is_banned') == 'yes'])
                active_users = total_users - banned_users
        except:
            total_users = banned_users = active_users = 0
        
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                transactions = list(csv.DictReader(f))
                total_trans = len(transactions)
                pending_trans = len([t for t in transactions if t['status'] == 'pending'])
                approved_trans = len([t for t in transactions if t['status'] == 'approved'])
                rejected_trans = len([t for t in transactions if t['status'] == 'rejected'])
                
                # حساب إجمالي المبالغ
                total_amount = sum(float(t.get('amount', 0)) for t in transactions if t['status'] == 'approved')
        except:
            total_trans = pending_trans = approved_trans = rejected_trans = 0
            total_amount = 0
        
        admin_text = f"""🛠️ لوحة التحكم الشاملة

📊 الإحصائيات الحية:
👥 المستخدمين: {total_users}
   ✅ نشطين: {active_users}
   🚫 محظورين: {banned_users}

💰 المعاملات: {total_trans}
   ⏳ معلقة: {pending_trans}
   ✅ مُوافقة: {approved_trans}
   ❌ مرفوضة: {rejected_trans}
   💵 إجمالي المبالغ: {total_amount:,.0f} ريال

استخدم الأزرار أدناه للتحكم الكامل:"""
        
        self.send_message(message['chat']['id'], admin_text, self.admin_keyboard())
    
    def show_approved_transactions(self, message):
        """عرض الطلبات المُوافقة"""
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                transactions = [t for t in csv.DictReader(f) if t['status'] == 'approved']
        except:
            transactions = []
        
        if not transactions:
            self.send_message(message['chat']['id'], "✅ لا توجد طلبات مُوافقة", self.admin_keyboard())
            return
        
        response = f"✅ الطلبات المُوافقة ({len(transactions)}):\n\n"
        for trans in transactions[-10:]:
            response += f"🆔 {trans['id']}\n👤 {trans['name']}\n💰 {trans['type']}: {trans['amount']} ريال\n📅 {trans['date']}\n\n"
        
        self.send_message(message['chat']['id'], response, self.admin_keyboard())
    
    def show_users_management(self, message):
        """إدارة المستخدمين"""
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                users = list(csv.DictReader(f))
        except:
            users = []
        
        if not users:
            self.send_message(message['chat']['id'], "👥 لا توجد مستخدمين", self.admin_keyboard())
            return
        
        active = [u for u in users if u.get('is_banned', 'no') == 'no']
        banned = [u for u in users if u.get('is_banned', 'no') == 'yes']
        
        response = f"""👥 إدارة المستخدمين

📊 الإحصائيات:
✅ نشطين: {len(active)}
🚫 محظورين: {len(banned)}
📋 المجموع: {len(users)}

آخر 5 مستخدمين:
"""
        for user in users[-5:]:
            status = "🚫" if user.get('is_banned') == 'yes' else "✅"
            response += f"{status} {user['name']} ({user['customer_id']})\n"
        
        self.send_message(message['chat']['id'], response, self.admin_keyboard())
    
    def prompt_admin_search(self, message):
        """طلب البحث من الأدمن"""
        response = "🔍 البحث في المستخدمين\n\nأرسل اسم العميل أو رقم العميل للبحث:"
        self.send_message(message['chat']['id'], response)
        self.user_states[message['from']['id']] = 'admin_searching'
    
    def show_payment_methods_admin(self, message):
        """عرض وسائل الدفع للأدمن"""
        deposit_methods = self.get_payment_methods('deposit')
        withdraw_methods = self.get_payment_methods('withdraw')
        
        response = "💳 وسائل الدفع الحالية\n\n"
        
        response += "💰 وسائل الإيداع:\n"
        for method in deposit_methods:
            response += f"🏦 {method['name']}\n"
        
        response += f"\n💸 وسائل السحب:\n"
        for method in withdraw_methods:
            response += f"💳 {method['name']}\n"
        
        response += f"\n📝 المجموع: {len(deposit_methods + withdraw_methods)}"
        
        self.send_message(message['chat']['id'], response, self.admin_keyboard())
    
    def show_detailed_stats(self, message):
        """إحصائيات تفصيلية"""
        # إحصائيات المستخدمين
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                users = list(csv.DictReader(f))
                total_users = len(users)
                banned_users = len([u for u in users if u.get('is_banned') == 'yes'])
                today_users = len([u for u in users if u['date'].startswith(datetime.now().strftime('%Y-%m-%d'))])
        except:
            total_users = banned_users = today_users = 0
        
        # إحصائيات المعاملات
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                transactions = list(csv.DictReader(f))
                total_trans = len(transactions)
                pending_trans = len([t for t in transactions if t['status'] == 'pending'])
                approved_trans = len([t for t in transactions if t['status'] == 'approved'])
                rejected_trans = len([t for t in transactions if t['status'] == 'rejected'])
                
                # المبالغ
                total_amount = sum(float(t.get('amount', 0)) for t in transactions if t['status'] == 'approved')
                pending_amount = sum(float(t.get('amount', 0)) for t in transactions if t['status'] == 'pending')
                
                # اليوم
                today = datetime.now().strftime('%Y-%m-%d')
                today_trans = [t for t in transactions if t['date'].startswith(today)]
                today_count = len(today_trans)
                today_amount = sum(float(t.get('amount', 0)) for t in today_trans if t['status'] == 'approved')
        except:
            total_trans = pending_trans = approved_trans = rejected_trans = 0
            total_amount = pending_amount = today_count = today_amount = 0
        
        response = f"""📊 الإحصائيات التفصيلية

👥 المستخدمين:
📋 المجموع: {total_users}
✅ نشطين: {total_users - banned_users}
🚫 محظورين: {banned_users}
🆕 اليوم: {today_users}

💰 المعاملات:
📋 المجموع: {total_trans}
⏳ معلقة: {pending_trans}
✅ مُوافقة: {approved_trans}
❌ مرفوضة: {rejected_trans}

💵 المبالغ:
✅ إجمالي مُوافق: {total_amount:,.0f} ريال
⏳ معلق: {pending_amount:,.0f} ريال

📈 إحصائيات اليوم:
📋 معاملات: {today_count}
💵 مبالغ: {today_amount:,.0f} ريال

📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        self.send_message(message['chat']['id'], response, self.admin_keyboard())
    
    def prompt_broadcast(self, message):
        """طلب الإرسال الجماعي"""
        response = "📢 الإرسال الجماعي\n\nأرسل الرسالة التي تريد إرسالها لجميع المستخدمين:"
        self.send_message(message['chat']['id'], response)
        self.user_states[message['from']['id']] = 'admin_broadcasting'
    
    def prompt_ban_user(self, message):
        """طلب حظر مستخدم"""
        response = "🚫 حظر مستخدم\n\nأرسل رقم العميل والسبب:\nمثال: C000001 مخالفة الشروط"
        self.send_message(message['chat']['id'], response)
        self.user_states[message['from']['id']] = 'admin_banning'
    
    def prompt_unban_user(self, message):
        """طلب إلغاء حظر مستخدم"""
        response = "✅ إلغاء حظر مستخدم\n\nأرسل رقم العميل:\nمثال: C000001"
        self.send_message(message['chat']['id'], response)
        self.user_states[message['from']['id']] = 'admin_unbanning'
    
    def create_withdrawal_request(self, message):
        """إنشاء طلب سحب متقدم مع اختيار الشركة"""
        user = self.find_user(message['from']['id'])
        if not user:
            return
        
        # عرض شركات السحب المتاحة
        withdraw_methods = self.get_payment_methods('withdraw')
        if not withdraw_methods:
            self.send_message(message['chat']['id'], "❌ لا توجد شركات سحب متاحة حالياً")
            return
        
        methods_text = "💸 طلب سحب جديد\n\nالشركات المتاحة للسحب:\n\n"
        keyboard_buttons = []
        
        for method in withdraw_methods:
            methods_text += f"💳 {method['name']}\n📝 {method['details']}\n\n"
            keyboard_buttons.append([{'text': f"💸 {method['name']}"}])
        
        keyboard_buttons.append([{'text': '🔙 العودة للقائمة الرئيسية'}])
        
        methods_text += "اختر الشركة المناسبة للسحب:"
        
        self.send_message(message['chat']['id'], methods_text, {
            'keyboard': keyboard_buttons,
            'resize_keyboard': True,
            'one_time_keyboard': True
        })
        
        self.user_states[message['from']['id']] = 'selecting_withdraw_method'
    
    def process_withdrawal_method_selection(self, message):
        """معالجة اختيار شركة السحب"""
        user = self.find_user(message['from']['id'])
        selected_method = message['text'].replace('💸 ', '')
        
        # البحث عن الشركة المختارة
        withdraw_methods = self.get_payment_methods('withdraw')
        selected_method_info = None
        for method in withdraw_methods:
            if method['name'] == selected_method:
                selected_method_info = method
                break
        
        if not selected_method_info:
            self.send_message(message['chat']['id'], "❌ شركة السحب غير صحيحة")
            return
        
        response = f"""💸 تم اختيار شركة السحب: {selected_method}

📝 تفاصيل الشركة:
{selected_method_info['details']}

💡 الآن يرجى إدخال رقم محفظتك أو حسابك في {selected_method}:

مثال: 0501234567"""
        
        self.send_message(message['chat']['id'], response)
        self.user_states[message['from']['id']] = f'withdraw_wallet_{selected_method}'
    
    def process_withdrawal_wallet(self, message):
        """معالجة رقم المحفظة"""
        user = self.find_user(message['from']['id'])
        wallet_number = message['text'].strip()
        user_id = message['from']['id']
        state = self.user_states.get(user_id, '')
        
        if not state.startswith('withdraw_wallet_'):
            return
        
        selected_method = state.replace('withdraw_wallet_', '')
        
        response = f"""✅ تم استلام رقم المحفظة: {wallet_number}
🏦 الشركة: {selected_method}

💰 الآن يرجى إدخال المبلغ المطلوب سحبه:

مثال: 500"""
        
        self.send_message(message['chat']['id'], response)
        self.user_states[user_id] = f'withdraw_amount_{selected_method}_{wallet_number}'
    
    def process_withdrawal_amount(self, message):
        """معالجة مبلغ السحب وإنشاء الطلب"""
        if not message['text'].isdigit():
            self.send_message(message['chat']['id'], "❌ يرجى إدخال مبلغ صحيح (أرقام فقط)")
            return
        
        amount = message['text']
        user_id = message['from']['id']
        user = self.find_user(user_id)
        state = self.user_states.get(user_id, '')
        
        if not state.startswith('withdraw_amount_'):
            return
        
        parts = state.replace('withdraw_amount_', '').split('_', 1)
        selected_method = parts[0]
        wallet_number = parts[1]
        
        # إنشاء المعاملة
        trans_id = f"WTH{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # حفظ المعاملة
        with open('transactions.csv', 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                trans_id, user['customer_id'], user['telegram_id'], user['name'], 
                'withdrawal', amount, 'pending', datetime.now().strftime('%Y-%m-%d %H:%M'), 
                '', selected_method, wallet_number, ''
            ])
        
        # رسالة التأكيد للعميل
        confirmation = f"""✅ تم إنشاء طلب السحب بنجاح!

🆔 رقم المعاملة: {trans_id}
👤 العميل: {user['name']} ({user['customer_id']})
🏦 الشركة: {selected_method}
💳 المحفظة: {wallet_number}
💰 المبلغ: {amount} ريال
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

⏳ سيتم مراجعة طلبك خلال 24 ساعة
🔔 سيتم إشعارك فور تغيير حالة الطلب"""
        
        # إشعار شامل فوري للأدمن
        admin_notification = f"""💸 طلب سحب جديد - مكتمل!

🆔 رقم المعاملة: {trans_id}
👤 العميل: {user['name']} ({user['customer_id']})
📱 تيليجرام: @{message['from'].get('username', 'غير متوفر')} ({user['telegram_id']})
📞 الهاتف: {user['phone']}
🏦 شركة السحب: {selected_method}
💳 رقم المحفظة: {wallet_number}
💰 المبلغ المطلوب: {amount} ريال
📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}

🎯 الطلب جاهز للمعالجة:
✅ استخدم: /approve {trans_id} للموافقة
❌ استخدم: /reject {trans_id} السبب للرفض
📋 استخدم: /pending للمراجعة"""
        
        self.notify_admins(admin_notification)
        
        self.send_message(message['chat']['id'], confirmation, self.main_keyboard(user.get('language', 'ar')))
        
        # حذف حالة المستخدم
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    def prompt_add_payment_method(self, message):
        """طلب إضافة وسيلة دفع جديدة"""
        response = """📝 إضافة وسيلة دفع جديدة

أرسل التفاصيل بالتنسيق التالي:
deposit اسم_البنك تفاصيل_الحساب
أو
withdraw اسم_الشركة تفاصيل_المحفظة

أمثلة:
deposit بنك الأهلي رقم الحساب: 1234567890, اسم المستفيد: شركة النظام

withdraw فودافون كاش رقم المحفظة: 01012345678"""
        
        self.send_message(message['chat']['id'], response)
        self.user_states[message['from']['id']] = 'admin_adding_payment'
    
    def show_edit_payment_methods(self, message):
        """عرض وسائل الدفع للتعديل"""
        all_methods = []
        try:
            with open('payment_methods.csv', 'r', encoding='utf-8-sig') as f:
                all_methods = list(csv.DictReader(f))
        except:
            pass
        
        if not all_methods:
            self.send_message(message['chat']['id'], "❌ لا توجد وسائل دفع", self.admin_keyboard())
            return
        
        response = "⚙️ تعديل وسائل الدفع\n\n"
        
        deposit_methods = [m for m in all_methods if m['type'] == 'deposit']
        withdraw_methods = [m for m in all_methods if m['type'] == 'withdraw']
        
        response += "💰 وسائل الإيداع:\n"
        for i, method in enumerate(deposit_methods, 1):
            status = "🟢" if method['is_active'] == 'active' else "🔴"
            response += f"{status} {i}. {method['name']}\n"
        
        response += f"\n💸 وسائل السحب:\n"
        for i, method in enumerate(withdraw_methods, 1):
            status = "🟢" if method['is_active'] == 'active' else "🔴"
            response += f"{status} {i}. {method['name']}\n"
        
        response += f"\n💡 لحذف وسيلة دفع: delete رقم_الوسيلة\nمثال: delete 1"
        
        self.send_message(message['chat']['id'], response, self.admin_keyboard())
        self.user_states[message['from']['id']] = 'admin_editing_payment'
    
    def handle_start(self, message):
        """بدء التسجيل"""
        user_info = message['from']
        user = self.find_user(user_info['id'])
        
        if not user:
            text = f"مرحباً {user_info['first_name']}! 🎉\n\nمرحباً بك في نظام LangSense المالي المتقدم\n\nيرجى مشاركة رقم هاتفك لإكمال التسجيل"
            keyboard = {
                'keyboard': [[{'text': '📱 مشاركة رقم الهاتف', 'request_contact': True}]],
                'resize_keyboard': True,
                'one_time_keyboard': True
            }
            self.send_message(message['chat']['id'], text, keyboard)
        else:
            if self.is_user_banned(user_info['id']):
                self.send_message(message['chat']['id'], f"🚫 حسابك محظور\nالسبب: {user.get('ban_reason', 'غير محدد')}\n\nتواصل مع الإدارة")
                return
            
            lang = user.get('language', 'ar')
            text = f"مرحباً {user['name']}! 👋\n🆔 رقم العميل: {user['customer_id']}\n\nاختر الخدمة المطلوبة:"
            self.send_message(message['chat']['id'], text, self.main_keyboard(lang))
    
    def handle_contact(self, message):
        """معالجة مشاركة الهاتف"""
        contact = message['contact']
        user_info = message['from']
        
        if contact['user_id'] == user_info['id']:
            customer_id = f"C{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            with open('users.csv', 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([
                    user_info['id'], user_info['first_name'], contact['phone_number'], 
                    customer_id, 'ar', datetime.now().strftime('%Y-%m-%d %H:%M'), 'no', ''
                ])
            
            text = f"✅ تم التسجيل بنجاح!\n📱 الهاتف: {contact['phone_number']}\n🆔 رقم العميل: {customer_id}\n\nيمكنك الآن استخدام جميع خدمات النظام"
            self.send_message(message['chat']['id'], text, self.main_keyboard())
    
    def process_deposit_amount(self, message):
        """معالجة مبلغ الإيداع"""
        if not message['text'].isdigit():
            self.send_message(message['chat']['id'], "❌ يرجى إدخال مبلغ صحيح (أرقام فقط)")
            return
        
        amount = message['text']
        user_id = message['from']['id']
        state = self.user_states.get(user_id, '')
        
        if not state.startswith('deposit_amount_'):
            return
        
        trans_id = state.replace('deposit_amount_', '')
        
        # تحديث المعاملة بالمبلغ
        transactions = []
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['id'] == trans_id:
                        row['amount'] = amount
                        row['status'] = 'pending'
                        row['receipt_info'] = 'awaiting_receipt'
                    transactions.append(row)
            
            with open('transactions.csv', 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['id', 'customer_id', 'telegram_id', 'name', 'type', 'amount', 'status', 'date', 'admin_note', 'payment_method', 'receipt_info', 'processed_by']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(transactions)
        except:
            pass
        
        # إشعار فوري محسن للأدمن مع تفاصيل كاملة
        user = self.find_user(user_id)
        admin_notification = f"""💰 طلب إيداع محدث - مرحلة 2

🆔 رقم المعاملة: {trans_id}
👤 العميل: {user['name']} ({user['customer_id']})
📱 تيليجرام: {user['telegram_id']}
💵 المبلغ المطلوب: {amount} ريال
📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}
🔢 المرحلة: انتظار إيصال التحويل

🎯 الطلب جاهز للمراجعة النهائية
📋 استخدم: /pending للمراجعة
✅ استخدم: /approve {trans_id} للموافقة
❌ استخدم: /reject {trans_id} السبب للرفض

🔔 سيتم إشعارك فور استلام الإيصال"""
        
        self.notify_admins(admin_notification)
        
        response = f"✅ تم استلام المبلغ: {amount} ريال\n\n📸 الآن يرجى إرسال صورة إيصال التحويل\n\nبعد إرسال الإيصال، سيتم مراجعة طلبك خلال 24 ساعة"
        
        self.send_message(message['chat']['id'], response)
        self.user_states[user_id] = f'deposit_receipt_{trans_id}'
    
    def process_admin_search(self, message):
        """معالجة البحث من الأدمن"""
        query = message['text']
        results = self.search_users(query)
        
        if not results:
            response = f"❌ لم يتم العثور على نتائج للبحث: {query}"
        else:
            response = f"🔍 نتائج البحث عن: {query}\n\n"
            for user in results:
                ban_status = "🚫 محظور" if user.get('is_banned') == 'yes' else "✅ نشط"
                response += f"👤 {user['name']}\n🆔 {user['customer_id']}\n📱 {user['phone']}\n🔸 {ban_status}\n\n"
        
        self.send_message(message['chat']['id'], response, self.admin_keyboard())
        del self.user_states[message['from']['id']]
    
    def process_admin_broadcast(self, message):
        """معالجة الإرسال الجماعي"""
        broadcast_message = message['text']
        users_count = 0
        success_count = 0
        
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                users = list(csv.DictReader(f))
                users_count = len(users)
                
                for user in users:
                    if user.get('is_banned', 'no') == 'no':
                        try:
                            self.send_message(user['telegram_id'], f"📢 إعلان من الإدارة:\n\n{broadcast_message}")
                            success_count += 1
                        except:
                            pass
        except:
            pass
        
        response = f"✅ تم إرسال الرسالة الجماعية\n\n📊 الإحصائيات:\n👥 إجمالي المستخدمين: {users_count}\n✅ تم الإرسال: {success_count}\n❌ فشل: {users_count - success_count}"
        
        self.send_message(message['chat']['id'], response, self.admin_keyboard())
        del self.user_states[message['from']['id']]
    
    def process_admin_ban(self, message):
        """معالجة حظر مستخدم"""
        parts = message['text'].split(' ', 1)
        if len(parts) < 2:
            self.send_message(message['chat']['id'], "❌ يرجى إدخال رقم العميل والسبب\nمثال: C000001 مخالفة الشروط", self.admin_keyboard())
            del self.user_states[message['from']['id']]
            return
        
        customer_id = parts[0]
        reason = parts[1] if len(parts) > 1 else 'لم يذكر سبب'
        
        if self.ban_user(customer_id, reason, str(message['from']['id'])):
            # البحث عن المستخدم لإرسال إشعار له
            user = None
            try:
                with open('users.csv', 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['customer_id'] == customer_id:
                            user = row
                            break
            except:
                pass
            
            if user:
                try:
                    self.send_message(user['telegram_id'], f"🚫 تم حظر حسابك\n\nالسبب: {reason}\n\nللاستفسار تواصل مع الإدارة")
                except:
                    pass
            
            response = f"✅ تم حظر العميل {customer_id} بنجاح\nالسبب: {reason}"
        else:
            response = f"❌ فشل في حظر العميل {customer_id}\nتأكد من رقم العميل"
        
        self.send_message(message['chat']['id'], response, self.admin_keyboard())
        del self.user_states[message['from']['id']]
    
    def process_admin_unban(self, message):
        """معالجة إلغاء حظر مستخدم"""
        customer_id = message['text'].strip()
        
        if self.unban_user(customer_id):
            # البحث عن المستخدم لإرسال إشعار له
            user = None
            try:
                with open('users.csv', 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['customer_id'] == customer_id:
                            user = row
                            break
            except:
                pass
            
            if user:
                try:
                    self.send_message(user['telegram_id'], f"✅ تم إلغاء حظر حسابك\n\nيمكنك الآن استخدام جميع الخدمات")
                except:
                    pass
            
            response = f"✅ تم إلغاء حظر العميل {customer_id} بنجاح"
        else:
            response = f"❌ فشل في إلغاء حظر العميل {customer_id}\nتأكد من رقم العميل"
        
        self.send_message(message['chat']['id'], response, self.admin_keyboard())
        del self.user_states[message['from']['id']]
    
    def unban_user(self, customer_id):
        """إلغاء حظر مستخدم"""
        users = []
        success = False
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['customer_id'] == customer_id:
                        row['is_banned'] = 'no'
                        row['ban_reason'] = ''
                        success = True
                    users.append(row)
            
            if success:
                with open('users.csv', 'w', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['telegram_id', 'name', 'phone', 'customer_id', 'language', 'date', 'is_banned', 'ban_reason']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(users)
        except:
            pass
        return success
    
    def process_admin_add_payment(self, message):
        """معالجة إضافة وسيلة دفع"""
        try:
            parts = message['text'].split(' ', 2)
            if len(parts) < 3:
                self.send_message(message['chat']['id'], "❌ تنسيق خاطئ. استخدم:\ndeposit اسم_البنك التفاصيل", self.admin_keyboard())
                del self.user_states[message['from']['id']]
                return
            
            method_type = parts[0]
            method_name = parts[1]
            method_details = parts[2]
            
            if method_type not in ['deposit', 'withdraw']:
                self.send_message(message['chat']['id'], "❌ النوع يجب أن يكون deposit أو withdraw", self.admin_keyboard())
                del self.user_states[message['from']['id']]
                return
            
            # إنشاء معرف جديد
            new_id = str(int(datetime.now().timestamp()))
            
            with open('payment_methods.csv', 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([new_id, method_name, method_type, method_details, 'active', datetime.now().strftime('%Y-%m-%d')])
            
            response = f"✅ تم إضافة وسيلة الدفع بنجاح!\n🆔 المعرف: {new_id}\n📝 {method_name} ({method_type})"
            
            self.send_message(message['chat']['id'], response, self.admin_keyboard())
            del self.user_states[message['from']['id']]
            
        except Exception as e:
            self.send_message(message['chat']['id'], f"❌ حدث خطأ: {str(e)}", self.admin_keyboard())
            del self.user_states[message['from']['id']]
    
    def process_admin_edit_payment(self, message):
        """معالجة تعديل/حذف وسائل الدفع"""
        text = message['text'].strip().lower()
        
        if text.startswith('delete '):
            try:
                method_id = text.split(' ')[1]
                
                # قراءة جميع الوسائل
                methods = []
                found = False
                with open('payment_methods.csv', 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['id'] != method_id:
                            methods.append(row)
                        else:
                            found = True
                
                if found:
                    # إعادة كتابة الملف بدون الوسيلة المحذوفة
                    with open('payment_methods.csv', 'w', newline='', encoding='utf-8-sig') as f:
                        fieldnames = ['id', 'name', 'type', 'details', 'is_active', 'created_date']
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(methods)
                    
                    response = f"✅ تم حذف وسيلة الدفع رقم {method_id}"
                else:
                    response = f"❌ لم يتم العثور على وسيلة دفع برقم {method_id}"
                    
            except:
                response = "❌ خطأ في الحذف. تأكد من الرقم"
        else:
            response = "❌ أمر غير مفهوم. استخدم: delete رقم_الوسيلة"
        
        self.send_message(message['chat']['id'], response, self.admin_keyboard())
        del self.user_states[message['from']['id']]
    
    def run(self):
        """تشغيل البوت"""
        test_result = self.api_call('getMe')
        if not test_result or not test_result.get('ok'):
            logger.error("❌ خطأ في التوكن!")
            return
        
        bot_info = test_result['result']
        logger.info(f"✅ النظام المتقدم يعمل: @{bot_info['username']}")
        
        while True:
            try:
                updates = self.get_updates()
                if updates and updates.get('ok'):
                    for update in updates['result']:
                        self.offset = update['update_id']
                        if 'message' in update:
                            message = update['message']
                            if 'text' in message:
                                if message['text'] == '/start':
                                    self.handle_start(message)
                                else:
                                    self.handle_text(message)
                            elif 'contact' in message:
                                self.handle_contact(message)
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("تم إيقاف النظام")
                break
            except Exception as e:
                logger.error(f"خطأ: {e}")
                time.sleep(3)

if __name__ == '__main__':
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ يرجى تعيين BOT_TOKEN")
        exit(1)
    
    bot = AdvancedLangSenseBot(bot_token)
    bot.run()