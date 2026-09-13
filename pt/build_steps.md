# دليل بناء المحاكاة خطوة بخطوة

## الحالة
ملف university.pkt محفوظ من Packet Tracer 9 بعد تجربة HSRP وإعادة Gi0/2 إلى العمل. التحقق جزئي؛ نجح HTTP التعليمي وPing خارجي لاحقًا في جلسة تشخيصية، لكن اختبارات الحماية واستمرارية الخدمة أثناء العطل وإعادة الفتح النهائية غير مكتملة. بعد الفتح انتظر التقارب ثم جدد DHCP باستخدام ipconfig /renew عند الحاجة. university.xml مصدر مولد قبل التشغيل وليس نسخة مفكوكة من الحفظ الأخير. يحتوي الحفظ الأصلي على 71 جهاز شبكة/طرفية و50 كائن Power Distribution أضافها المحاكي؛ هذه ليست أجهزة شبكة إضافية.

## 1. الأجهزة
- 2 × 3650-24PS: CORE-1/2.
- 10 × 2911: DIST-A1/A2 إلى DIST-E1/E2 (واجهات فرعية 802.1Q).
- 10 × 2960-24TT: ACC-A1/A2 إلى ACC-E1/E2.
- 3 × 2911: EDGE وISP وDHCP-1.
- 46 جهازًا تمثيليًا حسب design/endpoints.csv؛ Server-PT للويب وDNS والخارج، PC-PT للبقية.
- عدد الأجهزة الطرفية يمثل عينة تعليمية؛ أعداد VLSM أكبر للتخطيط المستقبلي.

## 2. التوصيل
اتبع كل صف في design/port_map.csv حرفيًا (88 رابطًا). استخدم نوع الكابل الملائم أو Automatic، ثم تحقق من أرقام المنافذ. لا توصل VLANs بين المباني عبر Layer 2.

## 3. تطبيق الإعداد
ابدأ Core ثم التوزيع ثم الوصول ثم DHCP-1 وEDGE وISP. أجب no عن Initial Configuration Dialog. ألصق الملف المناسب من configs/ في CLI من وضع User EXEC. راجع كل Invalid input. احفظ write memory.
قد يحتاج RSA في بعض نسخ المحاكاة صياغة `crypto key generate rsa` ثم اختيار 2048 عند الطلب بدل الصياغة أحادية السطر. تحقق من `show ip ssh` ولا تفترض توليد المفتاح لمجرد لصق الأمر.

## 4. إعداد الخدمات
DHCP-1 معد بالكامل عبر CLI. لا تستخدم DHCP إضافيًا على Server-PT بالتوازي.
- DNS-SERVER = 10.50.2.139: Static mask/gateway حسب design/endpoints.csv، Services > DNS > On.
- أضف edu.campus.example → 10.50.2.140.
- أضف www.external.example → 203.0.113.10.
- EDU-WEB: Static IP ثم Services > HTTP > On. صفحة تعريف الجامعة بسيطة تكفي.
- PUBLIC-WEB: IP 203.0.113.10 /24 وGateway 203.0.113.1 وHTTP On.
- IT-ADMIN = 10.50.3.10: Static حسب الجدول.
- كل endpoint مكتوب له DHCP: Desktop > IP Configuration > DHCP. لا تعطه IP ثابتًا داخل النطاق الديناميكي.
- أجهزة Security وDNS/Web وIT ثابتة حسب الجدول.

## 5. اختبار صغير قبل التوسيع
نفذ مبنى A مع Core وخدمات E أولًا. تحقق من HSRP وOSPF وDHCP Snooping وPort Security والمنافذ الفعلية. إذا غاب دعم ميزة عن الجهاز، وثق رسالة الخطأ واختر موديلًا يدعمها؛ لا تستبدل HSRP بـVRRP وتسميه مكافئًا للتكليف.

## 6. التحقق الأمني
من طالب: HTTP للتعليم يجب أن يعمل؛ Ping البوابة ممنوع عمدًا. من ضيف: DNS والخارج فقط. من IT: SSH للأجهزة. من إدارة: HR/Finance مسموح. اتبع tests/test_matrix.csv وسجل النتائج الفعلية.

## 7. HSRP Failover
سجل show standby قبل التعطل. شغّل Ping متكرر إلى 203.0.113.10 من A طالب أو Complex PDU دوري. أطفئ DIST-A1 من Physical أو أغلق الواجهة المناسبة، ثم سجل A2 Active وعدد الحزم المفقودة وعودة الاتصال. أعد A1 وتحقق من preempt. لا تعدّل ACL لتزييف نجاح Ping إلى وجهة محظورة.

## 8. حفظ التسليم
احفظ pt/university.pkt. أغلق وافتح الملف من جديد وكرر DHCP وOSPF وHSRP وHTTP/SSH والمنع. التقط أوامر tests/show_commands.txt من الأجهزة المناسبة؛ DHCP binding من DHCP-1 وSnooping/Port Security من Access.

## 9. قيود معلنة
الخادم DHCP-1 وACC-E2 وEDGE نقاط فشل منفردة. Voice يمثل عزلًا شبكيًا لا مكالمات. ACL لا تعزل مستخدمين داخل VLAN نفسها. تخصيصات الإنتاج تحتاج حصر أجهزة حقيقيًا ومراجعة منافذ/PoE/مسافات. كلمات الدخول داخل configs تجريبية منشورة وتغيّر للإنتاج.
