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
    
    def is_admin(self, telegram_id):
        """فحص صلاحية الأدمن"""
        admin_ids = os.getenv('ADMIN_USER_IDS', '').split(',')
        return str(telegram_id) in admin_ids
    
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
        
        # فحص حالات المستخدم
        if user_id in self.user_states:
            state = self.user_states[user_id]
            if state == 'selecting_deposit_method':
                self.process_deposit_method_selection(message)
                return
            elif state.startswith('deposit_amount_'):
                self.process_deposit_amount(message)
                return
        
        user = self.find_user(user_id)
        if not user:
            self.handle_start(message)
            return
        
        lang = user.get('language', 'ar')
        
        # معالجة القوائم
        if text in ['💰 طلب إيداع', '💰 Deposit Request']:
            self.create_deposit_request(message)
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
        """موافقة الأدمن على طلب"""
        if not self.is_admin(message['from']['id']):
            return
        
        parts = message['text'].split(' ', 1)
        if len(parts) < 2:
            return
        
        trans_id = parts[1]
        if self.update_transaction_status(trans_id, 'approved', 'تمت الموافقة', str(message['from']['id'])):
            # إشعار المستخدم
            trans_info = self.get_transaction_info(trans_id)
            if trans_info:
                self.send_message(trans_info['telegram_id'], f"✅ تمت الموافقة على طلبك\n🆔 {trans_id}\n💰 {trans_info['type']}: {trans_info['amount']} ريال")
            
            self.send_message(message['chat']['id'], f"✅ تمت الموافقة على الطلب {trans_id}")
        else:
            self.send_message(message['chat']['id'], f"❌ فشل في الموافقة على الطلب {trans_id}")
    
    def handle_admin_reject(self, message):
        """رفض طلب"""
        if not self.is_admin(message['from']['id']):
            return
        
        parts = message['text'].split(' ', 2)
        if len(parts) < 3:
            self.send_message(message['chat']['id'], "استخدم: /reject رقم_المعاملة السبب")
            return
        
        trans_id = parts[1]
        reason = parts[2]
        
        if self.update_transaction_status(trans_id, 'rejected', reason, str(message['from']['id'])):
            trans_info = self.get_transaction_info(trans_id)
            if trans_info:
                self.send_message(trans_info['telegram_id'], f"❌ تم رفض طلبك\n🆔 {trans_id}\nالسبب: {reason}")
            
            self.send_message(message['chat']['id'], f"✅ تم رفض الطلب {trans_id}")
        else:
            self.send_message(message['chat']['id'], f"❌ فشل في رفض الطلب {trans_id}")
    
    def handle_admin_panel(self, message):
        """لوحة إدارة شاملة"""
        if not self.is_admin(message['from']['id']):
            return
        
        # إحصائيات شاملة
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                users = list(csv.DictReader(f))
                total_users = len(users)
                banned_users = len([u for u in users if u.get('is_banned') == 'yes'])
        except:
            total_users = banned_users = 0
        
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                transactions = list(csv.DictReader(f))
                total_trans = len(transactions)
                pending_trans = len([t for t in transactions if t['status'] == 'pending'])
                approved_trans = len([t for t in transactions if t['status'] == 'approved'])
        except:
            total_trans = pending_trans = approved_trans = 0
        
        admin_text = f"""🛠️ لوحة الإدارة المتقدمة

📊 الإحصائيات:
👥 المستخدمين: {total_users} (🚫 محظور: {banned_users})
💰 المعاملات: {total_trans}
   ⏳ معلقة: {pending_trans}
   ✅ مُوافق عليها: {approved_trans}

🔍 البحث والإدارة:
/search اسم_أو_رقم - البحث عن مستخدم
/userinfo رقم_العميل - تفاصيل المستخدم
/ban رقم_العميل السبب - حظر مستخدم
/unban رقم_العميل - إلغاء الحظر

📋 إدارة الطلبات:
/pending - عرض الطلبات المعلقة
/approve رقم_المعاملة - الموافقة على طلب
/reject رقم_المعاملة السبب - رفض طلب
/note رقم_المعاملة التعليق - إضافة تعليق

💳 إدارة وسائل الدفع:
/payments - عرض وسائل الدفع
/addpay deposit "اسم_البنك" "التفاصيل" - إضافة وسيلة إيداع
/addpay withdraw "اسم_المحفظة" "التفاصيل" - إضافة وسيلة سحب

📢 أخرى:
/broadcast رسالة - إرسال جماعي
/stats - إحصائيات تفصيلية"""
        
        self.send_message(message['chat']['id'], admin_text)
    
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
        
        response = f"✅ تم استلام المبلغ: {amount} ريال\n\n📸 الآن يرجى إرسال صورة إيصال التحويل\n\nبعد إرسال الإيصال، سيتم مراجعة طلبك خلال 24 ساعة"
        
        self.send_message(message['chat']['id'], response)
        self.user_states[user_id] = f'deposit_receipt_{trans_id}'
    
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