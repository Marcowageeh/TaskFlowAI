#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import csv
import urllib.request
import urllib.parse
import logging
from datetime import datetime

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveLangSenseBot:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.user_states = {}
        self.init_files()
        self.admin_ids = self.get_admin_ids()
        
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
                writer.writerow(['id', 'customer_id', 'telegram_id', 'name', 'type', 'company', 'wallet_number', 'amount', 'exchange_address', 'status', 'date', 'admin_note', 'processed_by'])
        
        # ملف الشركات
        if not os.path.exists('companies.csv'):
            with open('companies.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'name', 'type', 'details', 'is_active'])
                # شركات افتراضية
                companies = [
                    ['1', 'STC Pay', 'both', 'محفظة إلكترونية', 'active'],
                    ['2', 'البنك الأهلي', 'deposit', 'حساب بنكي رقم: 1234567890', 'active'],
                    ['3', 'فودافون كاش', 'both', 'محفظة إلكترونية', 'active'],
                    ['4', 'بنك الراجحي', 'deposit', 'حساب بنكي رقم: 0987654321', 'active'],
                    ['5', 'مدى البنك الأهلي', 'withdraw', 'رقم الحساب للسحب', 'active']
                ]
                for company in companies:
                    writer.writerow(company)
        
        # ملف عناوين الصرافة
        if not os.path.exists('exchange_addresses.csv'):
            with open('exchange_addresses.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'address', 'is_active'])
                writer.writerow(['1', 'شارع الملك فهد، الرياض، مقابل مول الرياض - الدور الأول', 'yes'])
        
        # ملف الشكاوى
        if not os.path.exists('complaints.csv'):
            with open('complaints.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'customer_id', 'message', 'status', 'date', 'admin_response'])
        
        # ملف إعدادات النظام
        if not os.path.exists('system_settings.csv'):
            with open('system_settings.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['setting_key', 'setting_value', 'description'])
                settings = [
                    ['min_deposit', '50', 'أقل مبلغ إيداع'],
                    ['min_withdrawal', '100', 'أقل مبلغ سحب'],
                    ['max_daily_withdrawal', '10000', 'أقصى سحب يومي'],
                    ['support_phone', '+966501234567', 'رقم الدعم'],
                    ['company_name', 'LangSense Financial', 'اسم الشركة']
                ]
                for setting in settings:
                    writer.writerow(setting)
        
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
        """إشعار جميع الأدمن"""
        for admin_id in self.admin_ids:
            try:
                self.send_message(admin_id, message, self.admin_keyboard())
            except:
                pass
    
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
    
    def get_companies(self, service_type=None):
        """جلب الشركات النشطة"""
        companies = []
        try:
            with open('companies.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('is_active', 'active') == 'active':
                        if service_type is None or row['type'] in [service_type, 'both']:
                            companies.append(row)
        except:
            pass
        return companies
    
    def get_exchange_address(self):
        """جلب عنوان الصرافة النشط"""
        try:
            with open('exchange_addresses.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['is_active'] == 'yes':
                        return row['address']
        except:
            pass
        return "العنوان غير متوفر حالياً"
    
    def get_setting(self, key):
        """جلب إعداد النظام"""
        try:
            with open('system_settings.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['setting_key'] == key:
                        return row['setting_value']
        except:
            pass
        return None
    
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
    
    def admin_keyboard(self):
        """لوحة مفاتيح الأدمن الشاملة"""
        return {
            'keyboard': [
                [{'text': '📋 الطلبات المعلقة'}, {'text': '✅ طلبات مُوافقة'}],
                [{'text': '👥 إدارة المستخدمين'}, {'text': '🔍 البحث'}],
                [{'text': '💳 وسائل الدفع'}, {'text': '📊 الإحصائيات'}],
                [{'text': '📢 إرسال جماعي'}, {'text': '🚫 حظر مستخدم'}],
                [{'text': '✅ إلغاء حظر'}, {'text': '📝 إضافة شركة'}],
                [{'text': '⚙️ إدارة الشركات'}, {'text': '📍 إدارة العناوين'}],
                [{'text': '⚙️ إعدادات النظام'}, {'text': '📨 الشكاوى'}],
                [{'text': '🏠 القائمة الرئيسية'}]
            ],
            'resize_keyboard': True,
            'one_time_keyboard': False
        }
    
    def companies_keyboard(self, service_type):
        """لوحة اختيار الشركات"""
        companies = self.get_companies(service_type)
        keyboard = []
        for company in companies:
            keyboard.append([{'text': f"🏢 {company['name']}"}])
        keyboard.append([{'text': '🔙 العودة للقائمة الرئيسية'}])
        return {'keyboard': keyboard, 'resize_keyboard': True, 'one_time_keyboard': True}
    
    def handle_start(self, message):
        """معالج بداية المحادثة"""
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        
        # فحص إذا كان المستخدم موجود
        user = self.find_user(user_id)
        if user:
            if user.get('is_banned') == 'yes':
                ban_reason = user.get('ban_reason', 'غير محدد')
                self.send_message(chat_id, f"❌ تم حظر حسابك\nالسبب: {ban_reason}\n\nللاستفسار تواصل مع الإدارة")
                return
            
            welcome_text = f"مرحباً بعودتك {user['name']}! 👋\n🆔 رقم العميل: {user['customer_id']}"
            self.send_message(chat_id, welcome_text, self.main_keyboard(user.get('language', 'ar')))
        else:
            welcome_text = """مرحباً بك في نظام LangSense المالي المتقدم! 👋

🔹 خدمات الإيداع والسحب
🔹 دعم فني متخصص
🔹 أمان وموثوقية عالية

يرجى إرسال اسمك الكامل للتسجيل:"""
            self.send_message(chat_id, welcome_text)
            self.user_states[user_id] = 'registering_name'
    
    def handle_registration(self, message):
        """معالجة التسجيل"""
        user_id = message['from']['id']
        state = self.user_states.get(user_id)
        
        if state == 'registering_name':
            name = message['text'].strip()
            if len(name) < 2:
                self.send_message(message['chat']['id'], "❌ اسم قصير جداً. يرجى إدخال اسم صحيح:")
                return
            
            self.user_states[user_id] = f'registering_phone_{name}'
            self.send_message(message['chat']['id'], "ممتاز! الآن أرسل رقم هاتفك (مع رمز البلد):")
            
        elif state.startswith('registering_phone_'):
            name = state.replace('registering_phone_', '')
            phone = message['text'].strip()
            
            if len(phone) < 10:
                self.send_message(message['chat']['id'], "❌ رقم هاتف غير صحيح. يرجى إدخال رقم صحيح:")
                return
            
            # إنشاء رقم عميل تلقائي
            customer_id = f"C{str(int(datetime.now().timestamp()))[-6:]}"
            
            # حفظ المستخدم
            with open('users.csv', 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([user_id, name, phone, customer_id, 'ar', 
                               datetime.now().strftime('%Y-%m-%d'), 'no', ''])
            
            welcome_text = f"""✅ تم التسجيل بنجاح!

👤 الاسم: {name}
📱 الهاتف: {phone}
🆔 رقم العميل: {customer_id}
📅 تاريخ التسجيل: {datetime.now().strftime('%Y-%m-%d')}

يمكنك الآن استخدام جميع الخدمات المالية:"""
            
            self.send_message(message['chat']['id'], welcome_text, self.main_keyboard())
            del self.user_states[user_id]
            
            # إشعار الأدمن بعضو جديد
            admin_msg = f"""🆕 عضو جديد انضم للنظام

👤 الاسم: {name}
📱 الهاتف: {phone}
🆔 رقم العميل: {customer_id}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
            self.notify_admins(admin_msg)
    
    def create_deposit_request(self, message):
        """إنشاء طلب إيداع"""
        user = self.find_user(message['from']['id'])
        if not user:
            return
        
        # عرض الشركات المتاحة للإيداع
        deposit_companies = self.get_companies('deposit')
        if not deposit_companies:
            self.send_message(message['chat']['id'], "❌ لا توجد شركات متاحة للإيداع حالياً")
            return
        
        companies_text = "💰 طلب إيداع جديد\n\n🏢 اختر الشركة للإيداع:\n\n"
        for company in deposit_companies:
            companies_text += f"🔹 {company['name']} - {company['details']}\n"
        
        self.send_message(message['chat']['id'], companies_text, self.companies_keyboard('deposit'))
        self.user_states[message['from']['id']] = 'selecting_deposit_company'
    
    def create_withdrawal_request(self, message):
        """إنشاء طلب سحب"""
        user = self.find_user(message['from']['id'])
        if not user:
            return
        
        # عرض الشركات المتاحة للسحب
        withdraw_companies = self.get_companies('withdraw')
        if not withdraw_companies:
            self.send_message(message['chat']['id'], "❌ لا توجد شركات متاحة للسحب حالياً")
            return
        
        companies_text = "💸 طلب سحب جديد\n\n🏢 اختر الشركة للسحب:\n\n"
        for company in withdraw_companies:
            companies_text += f"🔹 {company['name']} - {company['details']}\n"
        
        self.send_message(message['chat']['id'], companies_text, self.companies_keyboard('withdraw'))
        self.user_states[message['from']['id']] = 'selecting_withdraw_company'
    
    def process_deposit_flow(self, message):
        """معالجة تدفق الإيداع الكامل"""
        user_id = message['from']['id']
        state = self.user_states.get(user_id, '')
        text = message['text']
        
        if state == 'selecting_deposit_company':
            # إزالة الرمز التعبيري من اسم الشركة
            selected_company_name = text.replace('🏢 ', '')
            
            # البحث عن الشركة المختارة
            companies = self.get_companies('deposit')
            selected_company = None
            for company in companies:
                if company['name'] == selected_company_name:
                    selected_company = company
                    break
            
            if not selected_company:
                self.send_message(message['chat']['id'], "❌ اختيار غير صحيح. يرجى اختيار شركة من القائمة:")
                return
            
            # الانتقال لمرحلة إدخال رقم المحفظة
            wallet_text = f"""تم اختيار: {selected_company['name']}

💳 الآن أدخل رقم محفظتك/حسابك في {selected_company['name']}:

📋 تفاصيل الشركة:
{selected_company['details']}"""
            
            self.send_message(message['chat']['id'], wallet_text)
            self.user_states[user_id] = f'deposit_wallet_{selected_company["id"]}_{selected_company["name"]}'
            
        elif state.startswith('deposit_wallet_'):
            parts = state.split('_', 2)
            company_id = parts[2]
            company_name = parts[3] if len(parts) > 3 else ''
            wallet_number = text.strip()
            
            if len(wallet_number) < 5:
                self.send_message(message['chat']['id'], "❌ رقم المحفظة/الحساب قصير جداً. يرجى إدخال رقم صحيح:")
                return
            
            # الانتقال لمرحلة إدخال المبلغ
            min_deposit = self.get_setting('min_deposit') or '50'
            amount_text = f"""✅ تم حفظ رقم المحفظة: {wallet_number}

💰 الآن أدخل المبلغ المطلوب إيداعه:

📌 أقل مبلغ للإيداع: {min_deposit} ريال
💡 أدخل المبلغ بالأرقام فقط (مثال: 500)"""
            
            self.send_message(message['chat']['id'], amount_text)
            self.user_states[user_id] = f'deposit_amount_{company_id}_{company_name}_{wallet_number}'
            
        elif state.startswith('deposit_amount_'):
            parts = state.split('_', 3)
            company_id = parts[2]
            company_name = parts[3]
            wallet_number = parts[4] if len(parts) > 4 else ''
            
            try:
                amount = float(text.strip())
                min_deposit = float(self.get_setting('min_deposit') or '50')
                
                if amount < min_deposit:
                    self.send_message(message['chat']['id'], f"❌ أقل مبلغ للإيداع {min_deposit} ريال. يرجى إدخال مبلغ أكبر:")
                    return
                    
            except ValueError:
                self.send_message(message['chat']['id'], "❌ مبلغ غير صحيح. يرجى إدخال رقم صحيح:")
                return
            
            # إنشاء المعاملة
            user = self.find_user(user_id)
            trans_id = f"DEP{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # حفظ المعاملة
            with open('transactions.csv', 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([trans_id, user['customer_id'], user['telegram_id'], user['name'], 
                               'deposit', company_name, wallet_number, amount, '', 'pending', 
                               datetime.now().strftime('%Y-%m-%d %H:%M'), '', ''])
            
            # رسالة تأكيد للعميل
            confirmation = f"""✅ تم إرسال طلب الإيداع بنجاح

🆔 رقم المعاملة: {trans_id}
👤 العميل: {user['name']} ({user['customer_id']})
🏢 الشركة: {company_name}
💳 رقم المحفظة: {wallet_number}
💰 المبلغ: {amount} ريال
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
⏳ الحالة: في انتظار المراجعة

سيتم إشعارك فور مراجعة طلبك."""
            
            self.send_message(message['chat']['id'], confirmation, self.main_keyboard(user.get('language', 'ar')))
            del self.user_states[user_id]
            
            # إشعار فوري للأدمن بطلب الإيداع
            for admin_id in self.admin_ids:
                try:
                    admin_notification = f"""🔔 طلب إيداع جديد

🆔 رقم المعاملة: {trans_id}
👤 العميل: {user['name']} ({user['customer_id']})
🏢 الشركة: {company_name}
💳 رقم المحفظة: {wallet_number}
💰 المبلغ: {amount} ريال
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

لمراجعة الطلب: موافقة {trans_id} أو رفض {trans_id} [سبب]"""
                    self.send_message(admin_id, admin_notification)
                except:
                    pass
    
    def process_withdrawal_flow(self, message):
        """معالجة تدفق السحب الكامل"""
        user_id = message['from']['id']
        state = self.user_states.get(user_id, '')
        text = message['text']
        
        if state == 'selecting_withdraw_company':
            # إزالة الرمز التعبيري من اسم الشركة
            selected_company_name = text.replace('🏢 ', '')
            
            # البحث عن الشركة المختارة
            companies = self.get_companies('withdraw')
            selected_company = None
            for company in companies:
                if company['name'] == selected_company_name:
                    selected_company = company
                    break
            
            if not selected_company:
                self.send_message(message['chat']['id'], "❌ اختيار غير صحيح. يرجى اختيار شركة من القائمة:")
                return
            
            # الانتقال لمرحلة إدخال رقم المحفظة
            wallet_text = f"""تم اختيار: {selected_company['name']}

💳 الآن أدخل رقم محفظتك/حسابك في {selected_company['name']}:

📋 تفاصيل الشركة:
{selected_company['details']}"""
            
            self.send_message(message['chat']['id'], wallet_text)
            self.user_states[user_id] = f'withdraw_wallet_{selected_company["id"]}_{selected_company["name"]}'
            
        elif state.startswith('withdraw_wallet_'):
            parts = state.split('_', 2)
            company_id = parts[2]
            company_name = parts[3] if len(parts) > 3 else ''
            wallet_number = text.strip()
            
            if len(wallet_number) < 5:
                self.send_message(message['chat']['id'], "❌ رقم المحفظة/الحساب قصير جداً. يرجى إدخال رقم صحيح:")
                return
            
            # الانتقال لمرحلة إدخال المبلغ
            min_withdrawal = self.get_setting('min_withdrawal') or '100'
            max_withdrawal = self.get_setting('max_daily_withdrawal') or '10000'
            amount_text = f"""✅ تم حفظ رقم المحفظة: {wallet_number}

💰 الآن أدخل المبلغ المطلوب سحبه:

📌 أقل مبلغ للسحب: {min_withdrawal} ريال
📌 أقصى مبلغ يومي: {max_withdrawal} ريال
💡 أدخل المبلغ بالأرقام فقط (مثال: 1000)"""
            
            self.send_message(message['chat']['id'], amount_text)
            self.user_states[user_id] = f'withdraw_amount_{company_id}_{company_name}_{wallet_number}'
            
        elif state.startswith('withdraw_amount_'):
            parts = state.split('_', 3)
            company_id = parts[2]
            company_name = parts[3]
            wallet_number = parts[4] if len(parts) > 4 else ''
            
            try:
                amount = float(text.strip())
                min_withdrawal = float(self.get_setting('min_withdrawal') or '100')
                max_withdrawal = float(self.get_setting('max_daily_withdrawal') or '10000')
                
                if amount < min_withdrawal:
                    self.send_message(message['chat']['id'], f"❌ أقل مبلغ للسحب {min_withdrawal} ريال. يرجى إدخال مبلغ أكبر:")
                    return
                
                if amount > max_withdrawal:
                    self.send_message(message['chat']['id'], f"❌ أقصى مبلغ للسحب اليومي {max_withdrawal} ريال. يرجى إدخال مبلغ أقل:")
                    return
                    
            except ValueError:
                self.send_message(message['chat']['id'], "❌ مبلغ غير صحيح. يرجى إدخال رقم صحيح:")
                return
            
            # عرض عنوان السحب الثابت وطلب كود التأكيد
            withdrawal_address = self.get_exchange_address()
            
            confirm_text = f"""✅ تم تأكيد المبلغ: {amount} ريال

📍 عنوان السحب: 
{withdrawal_address}

🔐 يرجى إرسال كود التأكيد:"""
            
            self.send_message(message['chat']['id'], confirm_text)
            self.user_states[user_id] = f'withdraw_confirmation_code_{company_id}_{company_name}_{wallet_number}_{amount}_{withdrawal_address}'
            

        elif state.startswith('withdraw_confirmation_code_'):
            # فصل البيانات من الحالة
            data_part = state.replace('withdraw_confirmation_code_', '')
            parts = data_part.split('_')
            company_id = parts[0] if len(parts) > 0 else ''
            company_name = parts[1] if len(parts) > 1 else ''
            wallet_number = parts[2] if len(parts) > 2 else ''
            amount = parts[3] if len(parts) > 3 else ''
            withdrawal_address = parts[4] if len(parts) > 4 else ''
            confirmation_code = text.strip()
            
            if len(confirmation_code) < 3:
                self.send_message(message['chat']['id'], "❌ كود التأكيد قصير جداً. يرجى إدخال كود صحيح:")
                return
            
            # التأكيد النهائي
            final_confirm_text = f"""📋 مراجعة نهائية لطلب السحب:

🏢 الشركة: {company_name}
💳 رقم المحفظة: {wallet_number}
💰 المبلغ: {amount} ريال
📍 عنوان السحب: {withdrawal_address}
🔐 كود التأكيد: {confirmation_code}

أرسل "تأكيد" لإرسال الطلب أو "إلغاء" للعودة"""
            
            self.send_message(message['chat']['id'], final_confirm_text)
            self.user_states[user_id] = f'withdraw_final_confirm_{company_id}_{company_name}_{wallet_number}_{amount}_{withdrawal_address}_{confirmation_code}'
            
        elif state.startswith('withdraw_final_confirm_'):
            # فصل البيانات من الحالة
            data_part = state.replace('withdraw_final_confirm_', '')
            parts = data_part.split('_')
            company_id = parts[0] if len(parts) > 0 else ''
            company_name = parts[1] if len(parts) > 1 else ''
            wallet_number = parts[2] if len(parts) > 2 else ''
            amount = parts[3] if len(parts) > 3 else ''
            withdrawal_address = parts[4] if len(parts) > 4 else ''
            confirmation_code = parts[5] if len(parts) > 5 else ''
            
            # احتمالات التأكيد المتعددة
            confirm_options = ['تأكيد', 'تاكيد', 'تأكييد', 'تاكييد', 'موافق', 'موافقة', 'اوافق', 'أوافق', 'نعم', 'ok', 'yes', 'confirm', 'اكيد', 'أكيد']
            cancel_options = ['إلغاء', 'الغاء', 'لا', 'no', 'cancel', 'رفض', 'توقف', 'إيقاف']
            
            text_clean = text.lower().strip()
            
            if any(opt in text_clean for opt in confirm_options):
                # إنشاء المعاملة
                user = self.find_user(user_id)
                trans_id = f"WTH{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # حفظ المعاملة مع عنوان السحب وكود التأكيد
                with open('transactions.csv', 'a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow([trans_id, user['customer_id'], user['telegram_id'], user['name'], 
                                   'withdraw', company_name, wallet_number, amount, withdrawal_address, 'pending', 
                                   datetime.now().strftime('%Y-%m-%d %H:%M'), confirmation_code, ''])
                
                # رسالة تأكيد للعميل
                confirmation_msg = f"""✅ تم إرسال طلب السحب بنجاح

🆔 رقم المعاملة: {trans_id}
👤 العميل: {user['name']} ({user['customer_id']})
🏢 الشركة: {company_name}
💳 رقم المحفظة: {wallet_number}
💰 المبلغ: {amount} ريال
📍 عنوان السحب: {withdrawal_address}
🔐 كود التأكيد: {confirmation_code}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
⏳ الحالة: في انتظار المراجعة

سيتم إشعارك فور الموافقة على طلبك."""
                
                self.send_message(message['chat']['id'], confirmation_msg, self.main_keyboard(user.get('language', 'ar')))
                del self.user_states[user_id]
                
                # إشعار فوري للأدمن
                for admin_id in self.admin_ids:
                    try:
                        admin_notification = f"""🔔 طلب سحب جديد

🆔 رقم المعاملة: {trans_id}
👤 العميل: {user['name']} ({user['customer_id']})
🏢 الشركة: {company_name}
💳 رقم المحفظة: {wallet_number}
💰 المبلغ: {amount} ريال
📍 عنوان السحب: {withdrawal_address}
🔐 كود التأكيد: {confirmation_code}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

لمراجعة الطلب: موافقة {trans_id} أو رفض {trans_id} [سبب]"""
                        self.send_message(admin_id, admin_notification)
                    except:
                        pass
                
            elif any(opt in text_clean for opt in cancel_options):
                self.send_message(message['chat']['id'], "تم إلغاء العملية", self.main_keyboard())
                del self.user_states[user_id]
            else:
                self.send_message(message['chat']['id'], "يرجى الإجابة بكلمة تأكيد (تأكيد، موافق، نعم) أو إلغاء (إلغاء، لا، رفض):")
            
        # (معالج قديم محذوف لأن نظام السحب تم تحديثه)
    
    def show_user_transactions(self, message):
        """عرض معاملات المستخدم"""
        user = self.find_user(message['from']['id'])
        if not user:
            return
        
        transactions_text = f"📋 طلبات العميل: {user['name']}\n\n"
        found_transactions = False
        
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['customer_id'] == user['customer_id']:
                        found_transactions = True
                        status_emoji = "⏳" if row['status'] == 'pending' else "✅" if row['status'] == 'approved' else "❌"
                        type_emoji = "💰" if row['type'] == 'deposit' else "💸"
                        
                        transactions_text += f"{status_emoji} {type_emoji} {row['id']}\n"
                        transactions_text += f"🏢 {row['company']}\n"
                        transactions_text += f"💰 {row['amount']} ريال\n"
                        transactions_text += f"📅 {row['date']}\n"
                        
                        if row['status'] == 'rejected' and row.get('admin_note'):
                            transactions_text += f"📝 السبب: {row['admin_note']}\n"
                        elif row['status'] == 'approved':
                            transactions_text += f"✅ تمت الموافقة\n"
                        elif row['status'] == 'pending':
                            transactions_text += f"⏳ قيد المراجعة\n"
                        
                        transactions_text += "\n"
        except:
            pass
        
        if not found_transactions:
            transactions_text += "لا توجد معاملات سابقة"
        
        self.send_message(message['chat']['id'], transactions_text, self.main_keyboard(user.get('language', 'ar')))
    
    def show_user_profile(self, message):
        """عرض ملف المستخدم"""
        user = self.find_user(message['from']['id'])
        if not user:
            return
        
        profile_text = f"""👤 ملف العميل

🆔 رقم العميل: {user['customer_id']}
📛 الاسم: {user['name']}
📱 الهاتف: {user['phone']}
📅 تاريخ التسجيل: {user['date']}
🌐 اللغة: {'العربية' if user.get('language') == 'ar' else 'English'}

🔸 حالة الحساب: {'🚫 محظور' if user.get('is_banned') == 'yes' else '✅ نشط'}"""
        
        if user.get('is_banned') == 'yes' and user.get('ban_reason'):
            profile_text += f"\n📝 سبب الحظر: {user['ban_reason']}"
        
        self.send_message(message['chat']['id'], profile_text, self.main_keyboard(user.get('language', 'ar')))
    
    def handle_admin_panel(self, message):
        """لوحة تحكم الأدمن الرئيسية"""
        if not self.is_admin(message['from']['id']):
            return
        
        admin_welcome = """🔧 لوحة تحكم الأدمن

مرحباً بك في لوحة التحكم الشاملة
استخدم الأزرار أدناه للتنقل"""
        
        self.send_message(message['chat']['id'], admin_welcome, self.admin_keyboard())
    
    def process_message(self, message):
        """معالج الرسائل الرئيسي"""
        if 'text' not in message:
            return
        
        text = message['text']
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        
        # بداية المحادثة
        if text == '/start':
            self.handle_start(message)
            return
        
        # معالجة التسجيل
        if user_id in self.user_states:
            state = self.user_states[user_id]
            if state.startswith('registering'):
                self.handle_registration(message)
                return
            elif 'deposit' in state:
                self.process_deposit_flow(message)
                return
            elif 'withdraw' in state:
                self.process_withdrawal_flow(message)
                return
        
        # فحص المستخدم المسجل
        user = self.find_user(user_id)
        if not user:
            self.handle_start(message)
            return
        
        # فحص الحظر
        if user.get('is_banned') == 'yes':
            ban_reason = user.get('ban_reason', 'غير محدد')
            self.send_message(chat_id, f"❌ تم حظر حسابك\nالسبب: {ban_reason}")
            return
        
        # معالجة أوامر الأدمن
        if self.is_admin(user_id):
            if text == '/admin':
                self.handle_admin_panel(message)
                return
            
            # معالجة حالات الأدمن الخاصة
            if user_id in self.user_states:
                admin_state = self.user_states[user_id]
                if admin_state == 'admin_broadcasting':
                    self.send_broadcast_message(message, text)
                    return
                elif admin_state.startswith('adding_company_'):
                    self.handle_company_wizard(message)
                    return
                elif admin_state.startswith('editing_company_') or admin_state == 'selecting_company_edit':
                    self.handle_company_edit_wizard(message)
                    return
                elif admin_state == 'confirming_company_delete':
                    self.handle_company_delete_confirmation(message)
                    return
                elif admin_state.startswith('deleting_company_'):
                    company_id = admin_state.replace('deleting_company_', '')
                    self.finalize_company_delete(message, company_id)
                    return
            
            # معالجة النصوص والأزرار للأدمن
            self.handle_admin_actions(message)
            return
        
        # معالجة القوائم الرئيسية للمستخدمين
        if text in ['💰 طلب إيداع', '💰 Deposit Request']:
            self.create_deposit_request(message)
        elif text in ['💸 طلب سحب', '💸 Withdrawal Request']:
            self.create_withdrawal_request(message)
        elif text in ['📋 طلباتي', '📋 My Requests']:
            self.show_user_transactions(message)
        elif text in ['👤 حسابي', '👤 Profile']:
            self.show_user_profile(message)
        elif text in ['📨 شكوى', '📨 Complaint']:
            self.handle_complaint_start(message)
        elif text in ['🆘 دعم', '🆘 Support']:
            support_text = f"""🆘 الدعم الفني

📞 رقم الهاتف: {self.get_setting('support_phone') or '+966501234567'}
⏰ ساعات العمل: 24/7
🏢 الشركة: {self.get_setting('company_name') or 'LangSense Financial'}

يمكنك أيضاً إرسال شكوى من خلال النظام"""
            self.send_message(chat_id, support_text, self.main_keyboard(user.get('language', 'ar')))
        elif text in ['🇺🇸 English', '🇸🇦 العربية']:
            self.handle_language_change(message, text)
        elif text in ['🔙 العودة للقائمة الرئيسية']:
            if user_id in self.user_states:
                del self.user_states[user_id]
            self.send_message(chat_id, "تم العودة للقائمة الرئيسية", self.main_keyboard(user.get('language', 'ar')))
        else:
            # معالجة حالات المستخدم الخاصة
            if user_id in self.user_states:
                state = self.user_states[user_id]
                if state == 'writing_complaint':
                    self.save_complaint(message, text)
                    return
            
            self.send_message(chat_id, "يرجى اختيار من القائمة:", self.main_keyboard(user.get('language', 'ar')))
    
    def handle_admin_actions(self, message):
        """معالجة إجراءات الأدمن"""
        text = message['text']
        chat_id = message['chat']['id']
        
        # الأزرار الرئيسية
        if text == '📋 الطلبات المعلقة':
            self.show_pending_requests(message)
        elif text == '✅ طلبات مُوافقة':
            self.show_approved_transactions(message)
        elif text == '👥 إدارة المستخدمين':
            self.show_users_management(message)
        elif text == '🔍 البحث':
            self.prompt_admin_search(message)
        elif text == '💳 وسائل الدفع':
            self.show_payment_methods_admin(message)
        elif text == '📊 الإحصائيات':
            self.show_detailed_stats(message)
        elif text == '📢 إرسال جماعي':
            self.prompt_broadcast(message)
        elif text == '🚫 حظر مستخدم':
            self.prompt_ban_user(message)
        elif text == '✅ إلغاء حظر':
            self.prompt_unban_user(message)
        elif text == '📝 إضافة شركة':
            self.start_add_company_wizard(message)
        elif text == '⚙️ إدارة الشركات':
            self.show_companies_management_enhanced(message)
        elif text == '➕ إضافة شركة جديدة':
            self.prompt_add_company(message)
        elif text == '✏️ تعديل شركة':
            self.prompt_edit_company(message)
        elif text == '🗑️ حذف شركة':
            self.prompt_delete_company(message)
        elif text == '🔄 تحديث القائمة':
            self.show_companies_management_enhanced(message)
        elif text == '↩️ العودة للوحة الأدمن':
            self.handle_admin_panel(message)
        elif text == '📍 إدارة العناوين':
            self.show_addresses_management(message)
        elif text == '⚙️ إعدادات النظام':
            self.show_system_settings(message)
        elif text == '📨 الشكاوى':
            self.show_complaints_admin(message)
        elif text == '🏠 القائمة الرئيسية':
            user = self.find_user(message['from']['id'])
            if user:
                self.send_message(chat_id, "تم العودة للقائمة الرئيسية", self.main_keyboard(user.get('language', 'ar')))
        
        # أوامر نصية للأدمن (مبسطة مع احتمالات متعددة)
        elif any(word in text.lower() for word in ['موافقة', 'موافق', 'اوافق', 'أوافق', 'قبول', 'مقبول', 'تأكيد', 'تاكيد', 'نعم']):
            # استخراج رقم المعاملة
            words = text.split()
            trans_id = None
            for word in words:
                if any(word.startswith(prefix) for prefix in ['DEP', 'WTH']):
                    trans_id = word
                    break
            
            if trans_id:
                self.approve_transaction(message, trans_id)
            else:
                self.send_message(message['chat']['id'], "❌ لم يتم العثور على رقم المعاملة. مثال: موافقة DEP123456", self.admin_keyboard())
                
        elif any(word in text.lower() for word in ['رفض', 'رافض', 'لا', 'مرفوض', 'إلغاء', 'الغاء', 'منع']):
            # استخراج رقم المعاملة والسبب
            words = text.split()
            trans_id = None
            reason_start = -1
            
            for i, word in enumerate(words):
                if any(word.startswith(prefix) for prefix in ['DEP', 'WTH']):
                    trans_id = word
                    reason_start = i + 1
                    break
            
            if trans_id:
                reason = ' '.join(words[reason_start:]) if reason_start != -1 and reason_start < len(words) else 'غير محدد'
                self.reject_transaction(message, trans_id, reason)
            else:
                self.send_message(message['chat']['id'], "❌ لم يتم العثور على رقم المعاملة. مثال: رفض DEP123456 سبب الرفض", self.admin_keyboard())
        elif text.startswith('بحث '):
            query = text.replace('بحث ', '')
            self.search_users_admin(message, query)
        elif text.startswith('حظر '):
            parts = text.replace('حظر ', '').split(' ', 1)
            customer_id = parts[0]
            reason = parts[1] if len(parts) > 1 else 'مخالفة الشروط'
            self.ban_user_admin(message, customer_id, reason)
        elif text.startswith('الغاء_حظر '):
            customer_id = text.replace('الغاء_حظر ', '')
            self.unban_user_admin(message, customer_id)
        elif text.startswith('اضافة_شركة '):
            self.add_company_simple(message, text)
        elif text.startswith('حذف_شركة '):
            company_id = text.replace('حذف_شركة ', '')
            self.delete_company_simple(message, company_id)
        elif text.startswith('عنوان_جديد '):
            new_address = text.replace('عنوان_جديد ', '')
            self.update_address_simple(message, new_address)
        elif any(word in text.lower() for word in ['عنوان', 'العنوان', 'تحديث_عنوان']):
            # استخراج العنوان الجديد
            new_address = text
            for word in ['عنوان', 'العنوان', 'تحديث_عنوان']:
                new_address = new_address.replace(word, '').strip()
            if new_address:
                self.update_address_simple(message, new_address)
            else:
                self.send_message(message['chat']['id'], "يرجى كتابة العنوان الجديد. مثال: عنوان شارع الملك فهد", self.admin_keyboard())
        elif text.startswith('تعديل_اعداد '):
            self.update_setting_simple(message, text)
        else:
            self.send_message(chat_id, "أمر غير مفهوم. استخدم الأزرار أو الأوامر الصحيحة.", self.admin_keyboard())
    
    def show_pending_requests(self, message):
        """عرض الطلبات المعلقة للأدمن"""
        pending_text = "📋 الطلبات المعلقة:\n\n"
        found_pending = False
        
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['status'] == 'pending':
                        found_pending = True
                        type_emoji = "💰" if row['type'] == 'deposit' else "💸"
                        
                        pending_text += f"{type_emoji} {row['id']}\n"
                        pending_text += f"👤 {row['name']} ({row['customer_id']})\n"
                        pending_text += f"🏢 {row['company']}\n"
                        pending_text += f"💳 {row['wallet_number']}\n"
                        pending_text += f"💰 {row['amount']} ريال\n"
                        
                        if row.get('exchange_address'):
                            pending_text += f"📍 {row['exchange_address']}\n"
                        
                        pending_text += f"📅 {row['date']}\n"
                        pending_text += f"▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️\n\n"
        except:
            pass
        
        if not found_pending:
            pending_text += "✅ لا توجد طلبات معلقة"
        else:
            pending_text += "\n📝 للموافقة: موافقة رقم_المعاملة"
            pending_text += "\n📝 للرفض: رفض رقم_المعاملة السبب"
        
        self.send_message(message['chat']['id'], pending_text, self.admin_keyboard())
    
    def approve_transaction(self, message, trans_id):
        """الموافقة على معاملة"""
        success = self.update_transaction_status(trans_id, 'approved', '', str(message['from']['id']))
        
        if success:
            # إشعار العميل
            transaction = self.get_transaction(trans_id)
            if transaction:
                customer_telegram_id = transaction.get('telegram_id')
                if customer_telegram_id:
                    type_text = "الإيداع" if transaction['type'] == 'deposit' else "السحب"
                    customer_msg = f"""✅ تمت الموافقة على طلب {type_text}

🆔 {trans_id}
💰 {transaction['amount']} ريال
🏢 {transaction['company']}
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'شكراً لك! تم تأكيد إيداعك.' if transaction['type'] == 'deposit' else 'يرجى زيارة مكتب الصرافة لاستلام المبلغ.'}"""
                    
                    user = self.find_user(customer_telegram_id)
                    lang = user.get('language', 'ar') if user else 'ar'
                    self.send_message(customer_telegram_id, customer_msg, self.main_keyboard(lang))
            
            self.send_message(message['chat']['id'], f"✅ تمت الموافقة على {trans_id}", self.admin_keyboard())
        else:
            self.send_message(message['chat']['id'], f"❌ فشل في الموافقة على {trans_id}", self.admin_keyboard())
    
    def reject_transaction(self, message, trans_id, reason):
        """رفض معاملة"""
        success = self.update_transaction_status(trans_id, 'rejected', reason, str(message['from']['id']))
        
        if success:
            # إشعار العميل
            transaction = self.get_transaction(trans_id)
            if transaction:
                customer_telegram_id = transaction.get('telegram_id')
                if customer_telegram_id:
                    type_text = "الإيداع" if transaction['type'] == 'deposit' else "السحب"
                    customer_msg = f"""❌ تم رفض طلب {type_text}

🆔 {trans_id}
💰 {transaction['amount']} ريال
📝 السبب: {reason}
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

يمكنك إنشاء طلب جديد أو التواصل مع الدعم."""
                    
                    user = self.find_user(customer_telegram_id)
                    lang = user.get('language', 'ar') if user else 'ar'
                    self.send_message(customer_telegram_id, customer_msg, self.main_keyboard(lang))
            
            self.send_message(message['chat']['id'], f"✅ تم رفض {trans_id}\nالسبب: {reason}", self.admin_keyboard())
        else:
            self.send_message(message['chat']['id'], f"❌ فشل في رفض {trans_id}", self.admin_keyboard())
    
    def update_transaction_status(self, trans_id, new_status, note='', admin_id=''):
        """تحديث حالة المعاملة"""
        transactions = []
        success = False
        
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['id'] == trans_id:
                        row['status'] = new_status
                        if note:
                            row['admin_note'] = note
                        if admin_id:
                            row['processed_by'] = admin_id
                        success = True
                    transactions.append(row)
            
            if success:
                with open('transactions.csv', 'w', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['id', 'customer_id', 'telegram_id', 'name', 'type', 'company', 'wallet_number', 'amount', 'exchange_address', 'status', 'date', 'admin_note', 'processed_by']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(transactions)
        except:
            pass
        
        return success
    
    def get_transaction(self, trans_id):
        """جلب معاملة محددة"""
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['id'] == trans_id:
                        return row
        except:
            pass
        return None
    
    def show_detailed_stats(self, message):
        """عرض إحصائيات مفصلة"""
        stats_text = "📊 إحصائيات النظام الشاملة\n\n"
        
        # إحصائيات المستخدمين
        total_users = 0
        banned_users = 0
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_users += 1
                    if row.get('is_banned') == 'yes':
                        banned_users += 1
        except:
            pass
        
        # إحصائيات المعاملات
        total_transactions = 0
        pending_count = 0
        approved_count = 0
        rejected_count = 0
        total_deposit_amount = 0
        total_withdraw_amount = 0
        
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_transactions += 1
                    amount = float(row.get('amount', 0))
                    
                    if row['status'] == 'pending':
                        pending_count += 1
                    elif row['status'] == 'approved':
                        approved_count += 1
                        if row['type'] == 'deposit':
                            total_deposit_amount += amount
                        else:
                            total_withdraw_amount += amount
                    elif row['status'] == 'rejected':
                        rejected_count += 1
        except:
            pass
        
        # إحصائيات الشكاوى
        total_complaints = 0
        try:
            with open('complaints.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                total_complaints = sum(1 for row in reader)
        except:
            pass
        
        stats_text += f"👥 المستخدمون:\n"
        stats_text += f"├ إجمالي المستخدمين: {total_users}\n"
        stats_text += f"├ المستخدمون النشطون: {total_users - banned_users}\n"
        stats_text += f"└ المستخدمون المحظورون: {banned_users}\n\n"
        
        stats_text += f"💰 المعاملات:\n"
        stats_text += f"├ إجمالي المعاملات: {total_transactions}\n"
        stats_text += f"├ معلقة: {pending_count}\n"
        stats_text += f"├ مُوافق عليها: {approved_count}\n"
        stats_text += f"└ مرفوضة: {rejected_count}\n\n"
        
        stats_text += f"💵 المبالغ المُوافق عليها:\n"
        stats_text += f"├ إجمالي الإيداعات: {total_deposit_amount:,.0f} ريال\n"
        stats_text += f"├ إجمالي السحوبات: {total_withdraw_amount:,.0f} ريال\n"
        stats_text += f"└ الفرق: {total_deposit_amount - total_withdraw_amount:,.0f} ريال\n\n"
        
        stats_text += f"📨 الشكاوى: {total_complaints}\n\n"
        stats_text += f"📅 تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        self.send_message(message['chat']['id'], stats_text, self.admin_keyboard())
    
    def add_company_simple(self, message, text):
        """إضافة شركة بصيغة مبسطة"""
        # تنسيق: اضافة_شركة اسم نوع تفاصيل
        parts = text.replace('اضافة_شركة ', '').split(' ', 2)
        if len(parts) < 3:
            help_text = """❌ طريقة إضافة الشركة:

📝 اكتب بالضبط:
اضافة_شركة اسم_الشركة نوع_الخدمة التفاصيل

🔹 أنواع الخدمة (بالإنجليزي):
• ايداع → deposit
• سحب → withdraw  
• ايداع وسحب → both

📋 أمثلة صحيحة:
▫️ اضافة_شركة مدى both محفظة_رقمية
▫️ اضافة_شركة البنك_الأهلي deposit حساب_بنكي
▫️ اضافة_شركة فودافون_كاش withdraw محفظة_الكترونية
▫️ اضافة_شركة STC_Pay both خدمات_دفع"""
            
            self.send_message(message['chat']['id'], help_text, self.admin_keyboard())
            return
        
        company_name = parts[0].replace('_', ' ')
        service_type = parts[1].lower()
        details = parts[2].replace('_', ' ')
        
        # قبول الكلمات العربية وتحويلها
        if service_type in ['ايداع', 'إيداع']:
            service_type = 'deposit'
        elif service_type in ['سحب']:
            service_type = 'withdraw'
        elif service_type in ['كلاهما', 'الكل', 'ايداع_وسحب']:
            service_type = 'both'
        
        if service_type not in ['deposit', 'withdraw', 'both']:
            error_text = """❌ نوع الخدمة خطأ!

✅ الأنواع المقبولة:
• deposit (للإيداع فقط)
• withdraw (للسحب فقط)
• both (للإيداع والسحب)

أو بالعربي:
• ايداع → deposit
• سحب → withdraw
• كلاهما → both

مثال صحيح:
اضافة_شركة مدى both محفظة_رقمية"""
            
            self.send_message(message['chat']['id'], error_text, self.admin_keyboard())
            return
        
        # إنشاء معرف جديد
        company_id = str(int(datetime.now().timestamp()))
        
        try:
            with open('companies.csv', 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([company_id, company_name, service_type, details, 'active'])
            
            success_msg = f"""✅ تم إضافة الشركة بنجاح

🆔 المعرف: {company_id}
🏢 الاسم: {company_name}
⚡ النوع: {service_type}
📋 التفاصيل: {details}"""
            
            self.send_message(message['chat']['id'], success_msg, self.admin_keyboard())
        except Exception as e:
            self.send_message(message['chat']['id'], f"❌ فشل في إضافة الشركة: {str(e)}", self.admin_keyboard())
    
    def update_address_simple(self, message, new_address):
        """تحديث عنوان الصرافة"""
        try:
            with open('exchange_addresses.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'address', 'is_active'])
                writer.writerow(['1', new_address, 'yes'])
            
            self.send_message(message['chat']['id'], f"✅ تم تحديث عنوان الصرافة:\n{new_address}", self.admin_keyboard())
        except Exception as e:
            self.send_message(message['chat']['id'], f"❌ فشل في تحديث العنوان: {str(e)}", self.admin_keyboard())
    
    def run(self):
        """تشغيل البوت"""
        logger.info(f"✅ النظام الشامل يعمل: @{os.getenv('BOT_TOKEN', 'unknown').split(':')[0] if os.getenv('BOT_TOKEN') else 'unknown'}")
        
        while True:
            try:
                updates = self.get_updates()
                if updates and updates.get('ok'):
                    for update in updates['result']:
                        self.offset = update['update_id']
                        
                        if 'message' in update:
                            self.process_message(update['message'])
                        elif 'callback_query' in update:
                            pass  # يمكن إضافة معالجة الأزرار المتقدمة لاحقاً
                            
            except KeyboardInterrupt:
                logger.info("تم إيقاف البوت")
                break
            except Exception as e:
                logger.error(f"خطأ: {e}")
                continue

    def handle_complaint_start(self, message):
        """بدء عملية الشكوى"""
        self.send_message(message['chat']['id'], "📨 أرسل شكواك أو استفسارك:")
        self.user_states[message['from']['id']] = 'writing_complaint'
    
    def handle_language_change(self, message, text):
        """تغيير اللغة"""
        user_id = message['from']['id']
        new_lang = 'en' if '🇺🇸' in text else 'ar'
        
        # تحديث لغة المستخدم في الملف
        users = []
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['telegram_id'] == str(user_id):
                        row['language'] = new_lang
                    users.append(row)
            
            with open('users.csv', 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['telegram_id', 'name', 'phone', 'customer_id', 'language', 'date', 'is_banned', 'ban_reason']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(users)
            
            welcome_msg = "Language changed to English!" if new_lang == 'en' else "تم تغيير اللغة إلى العربية!"
            self.send_message(message['chat']['id'], welcome_msg, self.main_keyboard(new_lang))
        except:
            pass
    
    def prompt_admin_search(self, message):
        """طلب البحث من الأدمن"""
        search_help = """🔍 البحث في النظام

أرسل: بحث متبوعاً بالنص المطلوب

يمكنك البحث بـ:
• اسم العميل
• رقم العميل
• رقم الهاتف

مثال: بحث أحمد"""
        self.send_message(message['chat']['id'], search_help, self.admin_keyboard())
    
    def prompt_broadcast(self, message):
        """طلب الإرسال الجماعي"""
        broadcast_help = """📢 الإرسال الجماعي

أرسل رسالة وسيتم إرسالها لجميع المستخدمين النشطين.
اكتب الرسالة مباشرة:"""
        self.send_message(message['chat']['id'], broadcast_help)
        self.user_states[message['from']['id']] = 'admin_broadcasting'
    
    def prompt_ban_user(self, message):
        """طلب حظر مستخدم"""
        ban_help = """🚫 حظر مستخدم

الصيغة: حظر رقم_العميل السبب

مثال: حظر C123456 مخالفة الشروط"""
        self.send_message(message['chat']['id'], ban_help, self.admin_keyboard())
    
    def prompt_unban_user(self, message):
        """طلب إلغاء حظر مستخدم"""
        unban_help = """✅ إلغاء حظر مستخدم

الصيغة: الغاء_حظر رقم_العميل

مثال: الغاء_حظر C123456"""
        self.send_message(message['chat']['id'], unban_help, self.admin_keyboard())
    
    def prompt_add_company(self, message):
        """بدء معالج إضافة شركة التفاعلي"""
        help_text = """🏢 معالج إضافة شركة جديدة
        
سأطلب منك المعلومات خطوة بخطوة:

📝 أولاً، أرسل اسم الشركة:
مثال: البنك الأهلي، مدى، STC Pay، فودافون كاش"""
        
        self.send_message(message['chat']['id'], help_text)
        self.user_states[message['from']['id']] = 'adding_company_name'
    
    def handle_company_wizard(self, message):
        """معالج إضافة الشركة التفاعلي"""
        user_id = message['from']['id']
        state = self.user_states.get(user_id)
        text = message.get('text', '').strip()
        
        if state == 'adding_company_name':
            # حفظ اسم الشركة
            if not hasattr(self, 'temp_company_data'):
                self.temp_company_data = {}
            if user_id not in self.temp_company_data:
                self.temp_company_data[user_id] = {}
            
            self.temp_company_data[user_id]['name'] = text
            
            # طلب نوع الخدمة
            service_keyboard = {
                'keyboard': [
                    [{'text': '💳 إيداع فقط'}, {'text': '💰 سحب فقط'}],
                    [{'text': '🔄 إيداع وسحب معاً'}],
                    [{'text': '❌ إلغاء'}]
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True
            }
            
            self.send_message(message['chat']['id'], 
                f"✅ تم حفظ اسم الشركة: {text}\n\n🔧 الآن اختر نوع الخدمة:", 
                service_keyboard)
            self.user_states[user_id] = 'adding_company_type'
            
        elif state == 'adding_company_type':
            # حفظ نوع الخدمة
            if text == '💳 إيداع فقط':
                service_type = 'deposit'
                service_display = 'إيداع فقط'
            elif text == '💰 سحب فقط':
                service_type = 'withdraw'
                service_display = 'سحب فقط'
            elif text == '🔄 إيداع وسحب معاً':
                service_type = 'both'
                service_display = 'إيداع وسحب'
            elif text == '❌ إلغاء':
                del self.user_states[user_id]
                if hasattr(self, 'temp_company_data') and user_id in self.temp_company_data:
                    del self.temp_company_data[user_id]
                self.send_message(message['chat']['id'], "❌ تم إلغاء إضافة الشركة", self.admin_keyboard())
                return
            else:
                self.send_message(message['chat']['id'], "❌ اختر نوع الخدمة من الأزرار المتاحة")
                return
            
            self.temp_company_data[user_id]['type'] = service_type
            self.temp_company_data[user_id]['type_display'] = service_display
            
            # طلب التفاصيل
            self.send_message(message['chat']['id'], 
                f"✅ نوع الخدمة: {service_display}\n\n📋 الآن أرسل تفاصيل الشركة:\nمثال: محفظة إلكترونية، حساب بنكي رقم 1234567890، خدمة دفع رقمية")
            self.user_states[user_id] = 'adding_company_details'
            
        elif state == 'adding_company_details':
            # حفظ التفاصيل وإنهاء العملية
            self.temp_company_data[user_id]['details'] = text
            
            # عرض ملخص التأكيد
            company_data = self.temp_company_data[user_id]
            confirm_text = f"""📊 ملخص الشركة الجديدة:

🏢 الاسم: {company_data['name']}
⚡ نوع الخدمة: {company_data['type_display']}
📋 التفاصيل: {company_data['details']}

هل تريد حفظ هذه الشركة؟"""
            
            confirm_keyboard = {
                'keyboard': [
                    [{'text': '✅ حفظ الشركة'}, {'text': '❌ إلغاء'}],
                    [{'text': '🔄 تعديل الاسم'}, {'text': '🔧 تعديل النوع'}, {'text': '📝 تعديل التفاصيل'}]
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True
            }
            
            self.send_message(message['chat']['id'], confirm_text, confirm_keyboard)
            self.user_states[user_id] = 'confirming_company'
            
        elif state == 'confirming_company':
            company_data = self.temp_company_data[user_id]
            
            if text == '✅ حفظ الشركة':
                # حفظ الشركة في الملف
                company_id = str(int(datetime.now().timestamp()))
                
                try:
                    with open('companies.csv', 'a', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f)
                        writer.writerow([company_id, company_data['name'], company_data['type'], company_data['details'], 'active'])
                    
                    success_msg = f"""🎉 تم إضافة الشركة بنجاح!

🆔 المعرف: {company_id}
🏢 الاسم: {company_data['name']}
⚡ النوع: {company_data['type_display']}
📋 التفاصيل: {company_data['details']}

الشركة متاحة الآن للعملاء ✅"""
                    
                    self.send_message(message['chat']['id'], success_msg, self.admin_keyboard())
                    
                except Exception as e:
                    self.send_message(message['chat']['id'], f"❌ فشل في حفظ الشركة: {str(e)}", self.admin_keyboard())
                
                # تنظيف البيانات المؤقتة
                del self.user_states[user_id]
                if user_id in self.temp_company_data:
                    del self.temp_company_data[user_id]
                    
            elif text == '❌ إلغاء':
                del self.user_states[user_id]
                if user_id in self.temp_company_data:
                    del self.temp_company_data[user_id]
                self.send_message(message['chat']['id'], "❌ تم إلغاء إضافة الشركة", self.admin_keyboard())
                
            elif text == '🔄 تعديل الاسم':
                self.send_message(message['chat']['id'], f"📝 الاسم الحالي: {company_data['name']}\n\nأرسل الاسم الجديد:")
                self.user_states[user_id] = 'adding_company_name'
                
            elif text == '🔧 تعديل النوع':
                service_keyboard = {
                    'keyboard': [
                        [{'text': '💳 إيداع فقط'}, {'text': '💰 سحب فقط'}],
                        [{'text': '🔄 إيداع وسحب معاً'}],
                        [{'text': '❌ إلغاء'}]
                    ],
                    'resize_keyboard': True,
                    'one_time_keyboard': True
                }
                self.send_message(message['chat']['id'], f"🔧 النوع الحالي: {company_data['type_display']}\n\nاختر النوع الجديد:", service_keyboard)
                self.user_states[user_id] = 'adding_company_type'
                
            elif text == '📝 تعديل التفاصيل':
                self.send_message(message['chat']['id'], f"📋 التفاصيل الحالية: {company_data['details']}\n\nأرسل التفاصيل الجديدة:")
                self.user_states[user_id] = 'adding_company_details'
                
            else:
                self.send_message(message['chat']['id'], "❌ اختر من الأزرار المتاحة")
    
    def prompt_edit_company(self, message):
        """بدء معالج تعديل الشركة"""
        # عرض الشركات المتاحة للتعديل
        companies_text = "🔧 تعديل الشركات:\n\n"
        
        try:
            with open('companies.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    status = "✅" if row.get('is_active') == 'active' else "❌"
                    companies_text += f"{status} {row['id']} - {row['name']}\n"
                    companies_text += f"   📋 {row['type']} - {row['details']}\n\n"
        except:
            companies_text += "❌ لا توجد شركات\n\n"
        
        companies_text += "📝 أرسل رقم معرف الشركة التي تريد تعديلها:"
        
        self.send_message(message['chat']['id'], companies_text)
        self.user_states[message['from']['id']] = 'selecting_company_edit'
    
    def handle_company_edit_wizard(self, message):
        """معالج تعديل الشركة التفاعلي"""
        user_id = message['from']['id']
        state = self.user_states.get(user_id)
        text = message.get('text', '').strip()
        
        if state == 'selecting_company_edit':
            # البحث عن الشركة
            company_found = None
            try:
                with open('companies.csv', 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['id'] == text:
                            company_found = row
                            break
            except:
                pass
            
            if not company_found:
                self.send_message(message['chat']['id'], f"❌ لم يتم العثور على شركة بالمعرف: {text}")
                return
            
            # حفظ بيانات الشركة للتعديل
            if not hasattr(self, 'edit_company_data'):
                self.edit_company_data = {}
            self.edit_company_data[user_id] = company_found
            
            # عرض بيانات الشركة الحالية
            type_display = {'deposit': 'إيداع فقط', 'withdraw': 'سحب فقط', 'both': 'إيداع وسحب'}.get(company_found['type'], company_found['type'])
            
            edit_options = f"""📊 بيانات الشركة الحالية:

🆔 المعرف: {company_found['id']}
🏢 الاسم: {company_found['name']}
⚡ النوع: {type_display}
📋 التفاصيل: {company_found['details']}
🔘 الحالة: {'نشط' if company_found.get('is_active') == 'active' else 'غير نشط'}

ماذا تريد تعديل؟"""
            
            edit_keyboard = {
                'keyboard': [
                    [{'text': '📝 تعديل الاسم'}, {'text': '🔧 تعديل النوع'}],
                    [{'text': '📋 تعديل التفاصيل'}, {'text': '🔘 تغيير الحالة'}],
                    [{'text': '✅ حفظ التغييرات'}, {'text': '❌ إلغاء'}]
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True
            }
            
            self.send_message(message['chat']['id'], edit_options, edit_keyboard)
            self.user_states[user_id] = 'editing_company_menu'
            
        elif state == 'editing_company_menu':
            if text == '📝 تعديل الاسم':
                current_name = self.edit_company_data[user_id]['name']
                self.send_message(message['chat']['id'], f"📝 الاسم الحالي: {current_name}\n\nأرسل الاسم الجديد:")
                self.user_states[user_id] = 'editing_company_name'
                
            elif text == '🔧 تعديل النوع':
                service_keyboard = {
                    'keyboard': [
                        [{'text': '💳 إيداع فقط'}, {'text': '💰 سحب فقط'}],
                        [{'text': '🔄 إيداع وسحب معاً'}],
                        [{'text': '↩️ العودة للقائمة'}]
                    ],
                    'resize_keyboard': True,
                    'one_time_keyboard': True
                }
                current_type = {'deposit': 'إيداع فقط', 'withdraw': 'سحب فقط', 'both': 'إيداع وسحب'}.get(self.edit_company_data[user_id]['type'])
                self.send_message(message['chat']['id'], f"🔧 النوع الحالي: {current_type}\n\nاختر النوع الجديد:", service_keyboard)
                self.user_states[user_id] = 'editing_company_type'
                
            elif text == '📋 تعديل التفاصيل':
                current_details = self.edit_company_data[user_id]['details']
                self.send_message(message['chat']['id'], f"📋 التفاصيل الحالية: {current_details}\n\nأرسل التفاصيل الجديدة:")
                self.user_states[user_id] = 'editing_company_details'
                
            elif text == '🔘 تغيير الحالة':
                current_status = self.edit_company_data[user_id].get('is_active', 'active')
                new_status = 'inactive' if current_status == 'active' else 'active'
                status_text = 'نشط' if new_status == 'active' else 'غير نشط'
                
                self.edit_company_data[user_id]['is_active'] = new_status
                self.send_message(message['chat']['id'], f"✅ تم تغيير حالة الشركة إلى: {status_text}")
                
                # العودة لقائمة التعديل
                self.show_edit_menu(message, user_id)
                
            elif text == '✅ حفظ التغييرات':
                self.save_company_changes(message, user_id)
                
            elif text == '❌ إلغاء':
                del self.user_states[user_id]
                if user_id in self.edit_company_data:
                    del self.edit_company_data[user_id]
                self.send_message(message['chat']['id'], "❌ تم إلغاء تعديل الشركة", self.admin_keyboard())
                
        elif state == 'editing_company_name':
            self.edit_company_data[user_id]['name'] = text
            self.send_message(message['chat']['id'], f"✅ تم تحديث الاسم إلى: {text}")
            self.show_edit_menu(message, user_id)
            
        elif state == 'editing_company_type':
            if text == '💳 إيداع فقط':
                self.edit_company_data[user_id]['type'] = 'deposit'
                self.send_message(message['chat']['id'], "✅ تم تحديث النوع إلى: إيداع فقط")
            elif text == '💰 سحب فقط':
                self.edit_company_data[user_id]['type'] = 'withdraw'
                self.send_message(message['chat']['id'], "✅ تم تحديث النوع إلى: سحب فقط")
            elif text == '🔄 إيداع وسحب معاً':
                self.edit_company_data[user_id]['type'] = 'both'
                self.send_message(message['chat']['id'], "✅ تم تحديث النوع إلى: إيداع وسحب")
            elif text == '↩️ العودة للقائمة':
                pass
            else:
                self.send_message(message['chat']['id'], "❌ اختر نوع الخدمة من الأزرار المتاحة")
                return
            
            self.show_edit_menu(message, user_id)
            
        elif state == 'editing_company_details':
            self.edit_company_data[user_id]['details'] = text
            self.send_message(message['chat']['id'], f"✅ تم تحديث التفاصيل إلى: {text}")
            self.show_edit_menu(message, user_id)
    
    def show_edit_menu(self, message, user_id):
        """عرض قائمة تعديل الشركة"""
        company_data = self.edit_company_data[user_id]
        type_display = {'deposit': 'إيداع فقط', 'withdraw': 'سحب فقط', 'both': 'إيداع وسحب'}.get(company_data['type'], company_data['type'])
        
        edit_options = f"""📊 بيانات الشركة المحدثة:

🆔 المعرف: {company_data['id']}
🏢 الاسم: {company_data['name']}
⚡ النوع: {type_display}
📋 التفاصيل: {company_data['details']}
🔘 الحالة: {'نشط' if company_data.get('is_active') == 'active' else 'غير نشط'}

ماذا تريد تعديل؟"""
        
        edit_keyboard = {
            'keyboard': [
                [{'text': '📝 تعديل الاسم'}, {'text': '🔧 تعديل النوع'}],
                [{'text': '📋 تعديل التفاصيل'}, {'text': '🔘 تغيير الحالة'}],
                [{'text': '✅ حفظ التغييرات'}, {'text': '❌ إلغاء'}]
            ],
            'resize_keyboard': True,
            'one_time_keyboard': True
        }
        
        self.send_message(message['chat']['id'], edit_options, edit_keyboard)
        self.user_states[user_id] = 'editing_company_menu'
    
    def save_company_changes(self, message, user_id):
        """حفظ تغييرات الشركة"""
        try:
            companies = []
            updated_company = self.edit_company_data[user_id]
            
            # قراءة جميع الشركات
            with open('companies.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['id'] == updated_company['id']:
                        companies.append(updated_company)
                    else:
                        companies.append(row)
            
            # كتابة الملف المحدث
            with open('companies.csv', 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['id', 'name', 'type', 'details', 'is_active']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(companies)
            
            type_display = {'deposit': 'إيداع فقط', 'withdraw': 'سحب فقط', 'both': 'إيداع وسحب'}.get(updated_company['type'])
            
            success_msg = f"""🎉 تم حفظ التغييرات بنجاح!

🆔 المعرف: {updated_company['id']}
🏢 الاسم: {updated_company['name']}
⚡ النوع: {type_display}
📋 التفاصيل: {updated_company['details']}
🔘 الحالة: {'نشط' if updated_company.get('is_active') == 'active' else 'غير نشط'}"""
            
            self.send_message(message['chat']['id'], success_msg, self.admin_keyboard())
            
        except Exception as e:
            self.send_message(message['chat']['id'], f"❌ فشل في حفظ التغييرات: {str(e)}", self.admin_keyboard())
        
        # تنظيف البيانات المؤقتة
        del self.user_states[user_id]
        if user_id in self.edit_company_data:
            del self.edit_company_data[user_id]
    
    def show_companies_management_enhanced(self, message):
        """عرض إدارة الشركات المحسن"""
        companies_text = "🏢 إدارة الشركات المتقدمة\n\n"
        
        try:
            with open('companies.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                company_count = 0
                for row in reader:
                    company_count += 1
                    status = "✅" if row.get('is_active') == 'active' else "❌"
                    type_display = {'deposit': 'إيداع', 'withdraw': 'سحب', 'both': 'الكل'}.get(row['type'], row['type'])
                    companies_text += f"{status} **{row['name']}** (ID: {row['id']})\n"
                    companies_text += f"   🔧 {type_display} | 📋 {row['details']}\n\n"
                
                if company_count == 0:
                    companies_text += "❌ لا توجد شركات مسجلة\n\n"
                else:
                    companies_text += f"📊 إجمالي الشركات: {company_count}\n\n"
                    
        except:
            companies_text += "❌ خطأ في قراءة ملف الشركات\n\n"
        
        # أزرار الإدارة المتقدمة
        management_keyboard = {
            'keyboard': [
                [{'text': '➕ إضافة شركة جديدة'}, {'text': '✏️ تعديل شركة'}],
                [{'text': '🗑️ حذف شركة'}, {'text': '🔄 تحديث القائمة'}],
                [{'text': '📋 تصدير البيانات'}, {'text': '↩️ العودة للوحة الأدمن'}]
            ],
            'resize_keyboard': True,
            'one_time_keyboard': True
        }
        
        companies_text += """🔧 خيارات الإدارة:
• ➕ إضافة شركة جديدة - معالج تفاعلي خطوة بخطوة
• ✏️ تعديل شركة - تعديل البيانات الموجودة
• 🗑️ حذف شركة - حذف نهائي بأمان
• 🔄 تحديث القائمة - إعادة تحميل البيانات"""
        
        self.send_message(message['chat']['id'], companies_text, management_keyboard)
    
    def prompt_delete_company(self, message):
        """بدء معالج حذف الشركة بأمان"""
        companies_text = "🗑️ حذف الشركات:\n\n"
        
        try:
            with open('companies.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    status = "✅" if row.get('is_active') == 'active' else "❌"
                    companies_text += f"{status} {row['id']} - {row['name']}\n"
                    companies_text += f"   📋 {row['type']} - {row['details']}\n\n"
        except:
            companies_text += "❌ لا توجد شركات\n\n"
        
        companies_text += "⚠️ أرسل رقم معرف الشركة للحذف:\n(تحذير: الحذف نهائي ولا يمكن التراجع عنه)"
        
        self.send_message(message['chat']['id'], companies_text)
        self.user_states[message['from']['id']] = 'confirming_company_delete'
    
    def handle_company_delete_confirmation(self, message):
        """معالج تأكيد حذف الشركة"""
        user_id = message['from']['id']
        text = message.get('text', '').strip()
        company_id = text
        
        # البحث عن الشركة
        company_found = None
        try:
            with open('companies.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['id'] == company_id:
                        company_found = row
                        break
        except:
            pass
        
        if not company_found:
            self.send_message(message['chat']['id'], f"❌ لم يتم العثور على شركة بالمعرف: {company_id}")
            del self.user_states[user_id]
            return
        
        # عرض تأكيد الحذف
        confirm_text = f"""⚠️ تأكيد حذف الشركة:

🆔 المعرف: {company_found['id']}
🏢 الاسم: {company_found['name']}
📋 النوع: {company_found['type']}
📝 التفاصيل: {company_found['details']}

⚠️ هذا الإجراء نهائي ولا يمكن التراجع عنه!
هل أنت متأكد من الحذف؟"""
        
        confirm_keyboard = {
            'keyboard': [
                [{'text': '🗑️ نعم، احذف الشركة'}, {'text': '❌ إلغاء'}]
            ],
            'resize_keyboard': True,
            'one_time_keyboard': True
        }
        
        self.send_message(message['chat']['id'], confirm_text, confirm_keyboard)
        self.user_states[user_id] = f'deleting_company_{company_id}'
    
    def finalize_company_delete(self, message, company_id):
        """إنهاء حذف الشركة"""
        user_id = message['from']['id']
        text = message.get('text', '').strip()
        
        if text == '🗑️ نعم، احذف الشركة':
            # تنفيذ الحذف
            companies = []
            deleted_company = None
            
            try:
                with open('companies.csv', 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['id'] != company_id:
                            companies.append(row)
                        else:
                            deleted_company = row
                
                # كتابة الملف بدون الشركة المحذوفة
                with open('companies.csv', 'w', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['id', 'name', 'type', 'details', 'is_active']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(companies)
                
                if deleted_company:
                    success_msg = f"""✅ تم حذف الشركة بنجاح!

🗑️ الشركة المحذوفة:
🆔 المعرف: {deleted_company['id']}
🏢 الاسم: {deleted_company['name']}
📋 النوع: {deleted_company['type']}"""
                    
                    self.send_message(message['chat']['id'], success_msg, self.admin_keyboard())
                else:
                    self.send_message(message['chat']['id'], "❌ فشل في العثور على الشركة للحذف", self.admin_keyboard())
                    
            except Exception as e:
                self.send_message(message['chat']['id'], f"❌ فشل في حذف الشركة: {str(e)}", self.admin_keyboard())
        
        elif text == '❌ إلغاء':
            self.send_message(message['chat']['id'], "❌ تم إلغاء حذف الشركة", self.admin_keyboard())
        
        # تنظيف الحالة
        del self.user_states[user_id]
    
    def start_add_company_wizard(self, message):
        """بدء معالج إضافة شركة تفاعلي"""
        wizard_text = """🧙‍♂️ معالج إضافة الشركة

سأساعدك في إضافة شركة بطريقة سهلة!

📝 أولاً: ما اسم الشركة؟
(مثال: بنك الراجحي، فودافون كاش، مدى)"""
        
        self.send_message(message['chat']['id'], wizard_text)
        self.user_states[message['from']['id']] = 'adding_company_name'
    
    def handle_add_company_wizard(self, message, text):
        """معالجة معالج إضافة الشركة"""
        user_id = message['from']['id']
        state = self.user_states.get(user_id, '')
        
        if state == 'adding_company_name':
            company_name = text.strip()
            if len(company_name) < 2:
                self.send_message(message['chat']['id'], "❌ اسم قصير جداً. أدخل اسم الشركة:")
                return
            
            # عرض أنواع الخدمة
            service_keyboard = {
                'keyboard': [
                    [{'text': '💰 إيداع فقط'}, {'text': '💸 سحب فقط'}],
                    [{'text': '🔄 إيداع وسحب معاً'}],
                    [{'text': '❌ إلغاء'}]
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True
            }
            
            self.send_message(message['chat']['id'], f"✅ اسم الشركة: {company_name}\n\n🔹 اختر نوع الخدمة:", service_keyboard)
            self.user_states[user_id] = f'adding_company_type_{company_name}'
            
        elif state.startswith('adding_company_type_'):
            company_name = state.replace('adding_company_type_', '')
            
            if text == '❌ إلغاء':
                self.send_message(message['chat']['id'], "تم إلغاء إضافة الشركة", self.admin_keyboard())
                del self.user_states[user_id]
                return
            
            # تحديد نوع الخدمة
            if text == '💰 إيداع فقط':
                service_type = 'deposit'
                service_ar = 'إيداع فقط'
            elif text == '💸 سحب فقط':
                service_type = 'withdraw'
                service_ar = 'سحب فقط'
            elif text == '🔄 إيداع وسحب معاً':
                service_type = 'both'
                service_ar = 'إيداع وسحب'
            else:
                self.send_message(message['chat']['id'], "❌ اختر من الأزرار المتاحة:")
                return
            
            self.send_message(message['chat']['id'], f"""✅ تم اختيار: {service_ar}

📝 الآن أدخل تفاصيل الشركة:
(مثال: حساب بنكي رقم 1234567890، محفظة إلكترونية، خدمات دفع متعددة)""")
            
            self.user_states[user_id] = f'adding_company_details_{company_name}_{service_type}'
            
        elif state.startswith('adding_company_details_'):
            parts = state.replace('adding_company_details_', '').rsplit('_', 1)
            company_name = parts[0]
            service_type = parts[1]
            details = text.strip()
            
            if len(details) < 3:
                self.send_message(message['chat']['id'], "❌ تفاصيل قصيرة جداً. أدخل وصف مناسب:")
                return
            
            # إنشاء الشركة
            company_id = str(int(datetime.now().timestamp()))
            
            try:
                with open('companies.csv', 'a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow([company_id, company_name, service_type, details, 'active'])
                
                service_ar = "إيداع فقط" if service_type == 'deposit' else "سحب فقط" if service_type == 'withdraw' else "إيداع وسحب"
                
                success_msg = f"""✅ تم إضافة الشركة بنجاح!

🆔 المعرف: {company_id}
🏢 الاسم: {company_name}
⚡ النوع: {service_ar}
📋 التفاصيل: {details}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

الشركة أصبحت متاحة الآن للعملاء."""
                
                self.send_message(message['chat']['id'], success_msg, self.admin_keyboard())
                del self.user_states[user_id]
                
            except Exception as e:
                self.send_message(message['chat']['id'], f"❌ فشل في إضافة الشركة: {str(e)}", self.admin_keyboard())
                del self.user_states[user_id]
    
    def show_companies_management(self, message):
        """عرض إدارة الشركات"""
        companies_text = "🏢 إدارة الشركات:\n\n"
        
        try:
            with open('companies.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    status = "✅" if row.get('is_active') == 'active' else "❌"
                    companies_text += f"{status} {row['id']} - {row['name']}\n"
                    companies_text += f"   📋 {row['type']} - {row['details']}\n\n"
        except:
            pass
        
        companies_text += "📝 الأوامر:\n"
        companies_text += "• اضافة_شركة اسم نوع تفاصيل\n"
        companies_text += "• حذف_شركة رقم_المعرف\n"
        
        self.send_message(message['chat']['id'], companies_text, self.admin_keyboard())
    
    def show_addresses_management(self, message):
        """عرض إدارة العناوين"""
        current_address = self.get_exchange_address()
        
        address_text = f"""📍 إدارة عناوين الصرافة

العنوان الحالي:
{current_address}

لتغيير العنوان:
عنوان_جديد النص_الجديد_للعنوان

مثال:
عنوان_جديد شارع الملك فهد، الرياض، مقابل برج المملكة"""
        
        self.send_message(message['chat']['id'], address_text, self.admin_keyboard())
    
    def show_system_settings(self, message):
        """عرض إعدادات النظام"""
        settings_text = "⚙️ إعدادات النظام:\n\n"
        
        try:
            with open('system_settings.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    settings_text += f"🔧 {row['setting_key']}: {row['setting_value']}\n"
                    settings_text += f"   📝 {row['description']}\n\n"
        except:
            pass
        
        settings_text += "📝 لتعديل إعداد:\n"
        settings_text += "تعديل_اعداد مفتاح_الإعداد القيمة_الجديدة\n\n"
        settings_text += "مثال:\nتعديل_اعداد min_deposit 100"
        
        self.send_message(message['chat']['id'], settings_text, self.admin_keyboard())
    
    def show_complaints_admin(self, message):
        """عرض الشكاوى للأدمن"""
        complaints_text = "📨 الشكاوى:\n\n"
        found_complaints = False
        
        try:
            with open('complaints.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    found_complaints = True
                    status = "✅ تم الرد" if row.get('admin_response') else "⏳ في انتظار الرد"
                    
                    complaints_text += f"🆔 {row['id']}\n"
                    complaints_text += f"👤 عميل: {row['customer_id']}\n"
                    complaints_text += f"📝 الشكوى: {row['message']}\n"
                    complaints_text += f"📅 التاريخ: {row['date']}\n"
                    complaints_text += f"🔸 {status}\n"
                    
                    if row.get('admin_response'):
                        complaints_text += f"💬 الرد: {row['admin_response']}\n"
                    
                    complaints_text += "\n"
        except:
            pass
        
        if not found_complaints:
            complaints_text += "لا توجد شكاوى"
        
        self.send_message(message['chat']['id'], complaints_text, self.admin_keyboard())
    
    def show_payment_methods_admin(self, message):
        """عرض وسائل الدفع للأدمن"""
        payment_text = """💳 وسائل الدفع المتاحة

هذا القسم يعرض الشركات المتاحة للإيداع والسحب.
استخدم 'إدارة الشركات' لإضافة أو تعديل وسائل الدفع."""
        
        companies = self.get_companies()
        for company in companies:
            service_type = "إيداع وسحب" if company['type'] == 'both' else "إيداع" if company['type'] == 'deposit' else "سحب"
            payment_text += f"\n🏢 {company['name']}\n"
            payment_text += f"   📋 {service_type} - {company['details']}\n"
        
        self.send_message(message['chat']['id'], payment_text, self.admin_keyboard())
    
    def ban_user_admin(self, message, customer_id, reason):
        """حظر مستخدم من قبل الأدمن"""
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
                
                self.send_message(message['chat']['id'], f"✅ تم حظر العميل {customer_id}\nالسبب: {reason}", self.admin_keyboard())
            else:
                self.send_message(message['chat']['id'], f"❌ لم يتم العثور على العميل {customer_id}", self.admin_keyboard())
        except:
            self.send_message(message['chat']['id'], "❌ فشل في حظر المستخدم", self.admin_keyboard())
    
    def unban_user_admin(self, message, customer_id):
        """إلغاء حظر مستخدم من قبل الأدمن"""
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
                
                self.send_message(message['chat']['id'], f"✅ تم إلغاء حظر العميل {customer_id}", self.admin_keyboard())
            else:
                self.send_message(message['chat']['id'], f"❌ لم يتم العثور على العميل {customer_id}", self.admin_keyboard())
        except:
            self.send_message(message['chat']['id'], "❌ فشل في إلغاء حظر المستخدم", self.admin_keyboard())
    
    def delete_company_simple(self, message, company_id):
        """حذف شركة بسيط"""
        companies = []
        deleted = False
        
        try:
            with open('companies.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['id'] != company_id:
                        companies.append(row)
                    else:
                        deleted = True
                        deleted_name = row['name']
            
            if deleted:
                with open('companies.csv', 'w', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['id', 'name', 'type', 'details', 'is_active']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(companies)
                
                self.send_message(message['chat']['id'], f"✅ تم حذف الشركة: {deleted_name} (ID: {company_id})", self.admin_keyboard())
            else:
                self.send_message(message['chat']['id'], f"❌ لم يتم العثور على شركة بالمعرف: {company_id}", self.admin_keyboard())
        except:
            self.send_message(message['chat']['id'], "❌ فشل في حذف الشركة", self.admin_keyboard())
    
    def update_setting_simple(self, message, text):
        """تحديث إعداد النظام"""
        # تنسيق: تعديل_اعداد مفتاح_الإعداد القيمة_الجديدة
        parts = text.replace('تعديل_اعداد ', '').split(' ', 1)
        if len(parts) < 2:
            help_text = """❌ تنسيق خاطئ

الصيغة الصحيحة:
تعديل_اعداد مفتاح_الإعداد القيمة_الجديدة

مثال:
تعديل_اعداد min_deposit 100"""
            self.send_message(message['chat']['id'], help_text, self.admin_keyboard())
            return
        
        setting_key = parts[0]
        setting_value = parts[1]
        
        settings = []
        updated = False
        
        try:
            with open('system_settings.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['setting_key'] == setting_key:
                        row['setting_value'] = setting_value
                        updated = True
                    settings.append(row)
            
            if updated:
                with open('system_settings.csv', 'w', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['setting_key', 'setting_value', 'description']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(settings)
                
                self.send_message(message['chat']['id'], f"✅ تم تحديث الإعداد:\n{setting_key} = {setting_value}", self.admin_keyboard())
            else:
                self.send_message(message['chat']['id'], f"❌ لم يتم العثور على الإعداد: {setting_key}", self.admin_keyboard())
        except:
            self.send_message(message['chat']['id'], "❌ فشل في تحديث الإعداد", self.admin_keyboard())
    
    def save_complaint(self, message, complaint_text):
        """حفظ شكوى المستخدم"""
        user = self.find_user(message['from']['id'])
        if not user:
            return
        
        complaint_id = f"COMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            with open('complaints.csv', 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([complaint_id, user['customer_id'], complaint_text, 'pending', 
                               datetime.now().strftime('%Y-%m-%d %H:%M'), ''])
            
            confirmation = f"""✅ تم إرسال شكواك بنجاح

🆔 رقم الشكوى: {complaint_id}
📝 المحتوى: {complaint_text}
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

سيتم الرد عليك في أقرب وقت ممكن."""
            
            self.send_message(message['chat']['id'], confirmation, self.main_keyboard(user.get('language', 'ar')))
            del self.user_states[message['from']['id']]
            
            # إشعار الأدمن بالشكوى الجديدة
            admin_msg = f"""📨 شكوى جديدة

🆔 {complaint_id}
👤 {user['name']} ({user['customer_id']})
📝 الشكوى: {complaint_text}
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
            
            self.notify_admins(admin_msg)
        except:
            self.send_message(message['chat']['id'], "❌ فشل في إرسال الشكوى. حاول مرة أخرى", self.main_keyboard(user.get('language', 'ar')))
            del self.user_states[message['from']['id']]
    
    def send_broadcast_message(self, message, broadcast_text):
        """إرسال رسالة جماعية"""
        sent_count = 0
        failed_count = 0
        
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                users = list(reader)
            
            # إرسال للمستخدمين النشطين فقط
            for user in users:
                if user.get('is_banned') != 'yes':
                    try:
                        broadcast_msg = f"""📢 رسالة من الإدارة

{broadcast_text}

📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
                        
                        result = self.send_message(user['telegram_id'], broadcast_msg, self.main_keyboard(user.get('language', 'ar')))
                        if result and result.get('ok'):
                            sent_count += 1
                        else:
                            failed_count += 1
                    except:
                        failed_count += 1
            
            summary = f"""✅ تم إرسال الرسالة الجماعية

📊 الإحصائيات:
• تم الإرسال بنجاح: {sent_count}
• فشل في الإرسال: {failed_count}
• إجمالي المحاولات: {sent_count + failed_count}

📝 الرسالة: {broadcast_text}"""
            
            self.send_message(message['chat']['id'], summary, self.admin_keyboard())
            del self.user_states[message['from']['id']]
        except:
            self.send_message(message['chat']['id'], "❌ فشل في الإرسال الجماعي", self.admin_keyboard())
            del self.user_states[message['from']['id']]

    def show_approved_transactions(self, message):
        """عرض المعاملات المُوافق عليها"""
        approved_text = "✅ المعاملات المُوافق عليها (آخر 20 معاملة):\n\n"
        found_approved = False
        count = 0
        
        try:
            with open('transactions.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                transactions = list(reader)
                
                # عكس الترتيب للحصول على أحدث المعاملات
                for row in reversed(transactions):
                    if row['status'] == 'approved' and count < 20:
                        found_approved = True
                        count += 1
                        type_emoji = "💰" if row['type'] == 'deposit' else "💸"
                        
                        approved_text += f"{type_emoji} {row['id']}\n"
                        approved_text += f"👤 {row['name']}\n"
                        approved_text += f"💰 {row['amount']} ريال\n"
                        approved_text += f"📅 {row['date']}\n\n"
        except:
            pass
        
        if not found_approved:
            approved_text += "لا توجد معاملات مُوافق عليها"
        
        self.send_message(message['chat']['id'], approved_text, self.admin_keyboard())
    
    def show_users_management(self, message):
        """عرض إدارة المستخدمين"""
        users_text = "👥 إدارة المستخدمين:\n\n"
        active_count = 0
        banned_count = 0
        
        try:
            with open('users.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('is_banned') == 'yes':
                        banned_count += 1
                    else:
                        active_count += 1
        except:
            pass
        
        users_text += f"✅ مستخدمون نشطون: {active_count}\n"
        users_text += f"🚫 مستخدمون محظورون: {banned_count}\n\n"
        
        users_text += "📝 الأوامر المتاحة:\n"
        users_text += "• بحث اسم_أو_رقم_العميل\n"
        users_text += "• حظر رقم_العميل السبب\n"
        users_text += "• الغاء_حظر رقم_العميل\n\n"
        
        users_text += "مثال:\nبحث أحمد\nحظر C123456 مخالفة_الشروط"
        
        self.send_message(message['chat']['id'], users_text, self.admin_keyboard())
    
    def search_users_admin(self, message, query):
        """البحث في المستخدمين للأدمن"""
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
        
        if not results:
            self.send_message(message['chat']['id'], f"❌ لم يتم العثور على نتائج للبحث: {query}", self.admin_keyboard())
            return
        
        search_text = f"🔍 نتائج البحث عن: {query}\n\n"
        for user in results[:10]:  # أول 10 نتائج فقط
            status = "🚫 محظور" if user.get('is_banned') == 'yes' else "✅ نشط"
            search_text += f"👤 {user['name']}\n"
            search_text += f"🆔 {user['customer_id']}\n"
            search_text += f"📱 {user['phone']}\n"
            search_text += f"🔸 {status}\n"
            if user.get('is_banned') == 'yes' and user.get('ban_reason'):
                search_text += f"📝 سبب الحظر: {user['ban_reason']}\n"
            search_text += "\n"
        
        self.send_message(message['chat']['id'], search_text, self.admin_keyboard())

if __name__ == "__main__":
    # جلب التوكن
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN غير موجود في متغيرات البيئة")
        exit(1)
    
    # تشغيل البوت
    bot = ComprehensiveLangSenseBot(bot_token)
    bot.run()