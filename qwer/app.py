from flask import Flask, render_template, abort, Response, request, redirect, session
from functools import wraps
import json, os, re, urllib.parse
 
app = Flask(__name__)
app.secret_key = "kz_admin_secret_2025"   # ← өзгертуге болады
 
# FIX: urlencode фильтрі — product_detail.html-де қолданылады
@app.template_filter('urlencode')
def urlencode_filter(s):
    return urllib.parse.quote(str(s))
 
# ============================================================
#  КОНФИГ
# ============================================================
ADMIN_PASSWORD = "admin123"          # ← паролді өзгерт!
BASE_URL       = "https://kaznur-ylttuk-keuym.onrender.com"
CONTACT_PHONE  = "77773988869"
CONTACT_DISPLAY= "+7 777 398 8869"
SITE_NAME      = "KZ Ұлттық киімдер дүкені"
SITE_DESC      = "Қазақстанның дәстүрлі ұлттық киімдері. Камзол, шапан, күртеше."
PRODUCTS_FILE  = "products.json"     # товарлар сақталатын файл
 
# ============================================================
#  JSON-ДАН ТОВАРЛАР ОҚУ / ЖАЗУ
# ============================================================
DEFAULT_PRODUCTS = {
    "1":  {"id":1,"slug":"ulttyk-kurteshe-konyr-altyn","title":"Ұлттық күртеше 1","price":"16 000 ₸","price_num":16000,"image":"dress1.1.png","detail_image":"dress1.jpg","theme":"theme-1","category":"men","description":"Дәстүрлі қазақы ою-өрнекпен безендірілген, табиғи мақта-зығыр матадан тігілген жоғары сапалы ұлттық күртеше.","material":"Жоғары сапалы мақта-зығыр","color":"Қоңыр / Алтын","sizes":["S","M","L","XL"]},
    "2":  {"id":2,"slug":"ulttyk-kurteshe-jasyl-krem","title":"Ұлттық күртеше 2","price":"16 000 ₸","price_num":16000,"image":"dress2.1.png","detail_image":"dress2.jpg","theme":"theme-2","category":"men","description":"Жасыл реңкті ою-өрнектермен безендірілген, жеңіл және әдемі ұлттық киім.","material":"Жоғары сапалы мақта","color":"Жасыл / Крем","sizes":["S","M","L","XL"]},
    "3":  {"id":3,"slug":"ulttyk-kurteshe-konyr-jasyl","title":"Ұлттық күртеше 3","price":"16 000 ₸","price_num":16000,"image":"dress3.1.png","detail_image":"dress3.jpg","theme":"theme-3","category":"men","description":"Жылы тондар мен дәстүрлі өрнектері бар сәнді ұлттық күртеше.","material":"Зығыр-мақта қоспасы","color":"Қоңыр / Жасыл","sizes":["S","M","L","XL"]},
    "4":  {"id":4,"slug":"ulttyk-kurteshe-altyn-sary","title":"Ұлттық күртеше 4","price":"16 000 ₸","price_num":16000,"image":"dress4.1.png","detail_image":"dress4.jpg","theme":"theme-4","category":"men","description":"Алтын реңкті ою-өрнектермен безендірілген ерлерге арналған ұлттық киім.","material":"Жоғары сапалы мақта","color":"Алтын / Сары","sizes":["S","M","L","XL","XXL"]},
    "5":  {"id":5,"slug":"ulttyk-kurteshe-bala-kok-ak","title":"Ұлттық күртеше 5","price":"16 000 ₸","price_num":16000,"image":"dress5.1.png","detail_image":"dress5.jpg","theme":"theme-5","category":"men","description":"Балаларға арналған ұлттық киім. Жеңіл, ыңғайлы және мейрамдарға жарайды.","material":"Жұмсақ мақта","color":"Аспан көк / Ақ","sizes":["3-4 жас","5-6 жас","7-8 жас","9-10 жас"]},
    "6":  {"id":6,"slug":"ulttyk-kurteshe-kok-sur","title":"Ұлттық күртеше 6","price":"16 000 ₸","price_num":16000,"image":"dress6.1.png","detail_image":"dress6.jpg","theme":"theme-6","category":"men","description":"Балаларға арналған, сыртқы ою-өрнектермен безендірілген ұлттық киім.","material":"Жұмсақ мақта-зығыр","color":"Көк / Сұр","sizes":[]},
    "7":  {"id":7,"slug":"ulttyk-kurteshe-kyzgyltsary-altyn","title":"Ұлттық күртеше 7","price":"16 000 ₸","price_num":16000,"image":"dress7.1.png","detail_image":"dress7.jpg","theme":"theme-7","category":"men","description":"Жылы реңктер мен дәстүрлі қазақы өрнектері бар ерлерге арналған ұлттық киім.","material":"Жоғары сапалы мақта","color":"Қызғылт сары / Алтын","sizes":["M","L","XL","XXL"]},
    "8":  {"id":8,"slug":"kamzol-kara-jasyl-barkyt","title":"Ұлттық күртеше 8","price":"16 000 ₸","price_num":16000,"image":"dress8.1.png","detail_image":"dress8.jpg","theme":"theme-8","category":"women","description":"Қымқа/барқыт матадан тігілген, зәйтүн түсті жакет.","material":"Жылтыр барқыт мата","color":"Қара Жасыл / Жасыл","sizes":["S","M","L","XL"]},
    "9":  {"id":9,"slug":"kamzol-zaituyn-barkyt-sandyk","title":"Ұлттық күртеше 9","price":"16 000 ₸","price_num":16000,"image":"dress9.1.png","detail_image":"dress9.jpg","theme":"theme-9","category":"women","description":"Барқыттан тігілген сәнді жакет (камзол үлгісінде).","material":"Қанық зәйтүн барқыт мата","color":"Оливковый түсті","sizes":["S","M","L","XL"]},
    "10": {"id":10,"slug":"shapan-kulgyn-barkyt-uzyn","title":"Ұлттық күртеше 10","price":"16 000 ₸","price_num":16000,"image":"dress10.1.png","detail_image":"dress10.jpg","theme":"theme-10","category":"women","description":"Ұзартылған пішілген барқыт шапан (кардиган).","material":"Орташа сапалы мақта-зығыр","color":"Қанық қою күлгін","sizes":["S","M","L","XL"]},
    "11": {"id":11,"slug":"kazhekey-koge-bala-barkyt","title":"Ұлттық күртеше 11","price":"16 000 ₸","price_num":16000,"image":"dress11.1.png","detail_image":"dress11.jpg","theme":"theme-11","category":"kids","description":"Қазақтың дәстүрлі кәжекейі (жеңсіз қамзолы).","material":"Жұмсақ жылтыр барқыт","color":"Көгілдір түсті","sizes":["S","M","L","XL"]},
    "12": {"id":12,"slug":"kazhekey-ashyk-kok-bala-barkyt","title":"Ұлттық күртеше 12","price":"16 000 ₸","price_num":16000,"image":"dress12.1.png","detail_image":"dress12.jpg","theme":"theme-12","category":"kids","description":"Жеңсіз дәстүрлі қазақ кәжекейі.","material":"Жылтыр барқыт (велюр)","color":"Ашық көк түсті","sizes":["S","M","L","XL"]},
    "13": {"id":13,"slug":"shapan-er-ashyk-kok-barkyt","title":"Ұлттық күртеше 13","price":"16 000 ₸","price_num":16000,"image":"dress13.1.png","detail_image":"dress13.jpg","theme":"theme-10","category":"men","description":"Ерлерге арналған стильді шапан.","material":"Барқыт немесе замш тектес мата","color":"Ашық көк түсті","sizes":["S","M","L","XL"]},
    "14": {"id":14,"slug":"shapan-er-konyr-kok-saltanat","title":"Ұлттық күртеше 14","price":"16 000 ₸","price_num":16000,"image":"dress14.1.png","detail_image":"dress14.jpg","theme":"theme-14","category":"men","description":"Ерлерге арналған салтанатты шапан.","material":"Жұмсақ барқыт матасы","color":"Қанық қою көк","sizes":["S","M","L","XL"]},
    "15": {"id":15,"slug":"bomber-qyz-borda-barkyt","title":"Ұлттық күртеше 15","price":"16 000 ₸","price_num":16000,"image":"dress15.1.png","detail_image":"dress15.jpg","theme":"theme-15","category":"women","description":"Заманауи үлгідегі қыздарға арналған бомбер-жакет.","material":"Жұмсақ барқыт матасы","color":"Қою шие (бордо)","sizes":["S","M","L","XL"]},
}
 
def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    save_products(DEFAULT_PRODUCTS)
    return DEFAULT_PRODUCTS
 
def save_products(data):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
 
KK_MAP = str.maketrans('ұүқғңөіәһ', 'uukgnoiah')
def slugify(text):
    text = text.lower().strip().translate(KK_MAP)
    text = re.sub(r'[а-яёa-z0-9\s-]', lambda m: m.group() if re.match(r'[a-z0-9\s-]', m.group()) else '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:60]
 
# ============================================================
#  HELPERS
# ============================================================
def format_price(n):
    return f"{int(n):,}".replace(',', ' ') + ' ₸'
 
def get_products_list():
    return list(load_products().values())
 
def get_product_by_slug(slug):
    return next((p for p in get_products_list() if p['slug'] == slug), None)
 
def get_related(product, count=3):
    return [p for p in get_products_list()
            if p['category'] == product['category'] and p['id'] != product['id']][:count]
 
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated
 
# ============================================================
#  САЙТ МАРШРУТТАРЫ
# ============================================================
@app.route('/')
def index():
    return render_template('index.html', products=get_products_list(),
                           contact=CONTACT_DISPLAY, phone=CONTACT_PHONE,
                           site_name=SITE_NAME, site_description=SITE_DESC)
 
@app.route('/women')
def women():
    filtered = [p for p in get_products_list() if p['category'] == 'women']
    return render_template('category.html', products=filtered, category="Қыздар",
                           category_en="women", category_desc="Қыздарға арналған қазақ ұлттық камзол мен күртеше.",
                           contact=CONTACT_DISPLAY, phone=CONTACT_PHONE, site_name=SITE_NAME)
 
@app.route('/men')
def men():
    filtered = [p for p in get_products_list() if p['category'] == 'men']
    return render_template('category.html', products=filtered, category="Ұлдар",
                           category_en="men", category_desc="Ерлерге арналған ұлттық шапан мен камзол.",
                           contact=CONTACT_DISPLAY, phone=CONTACT_PHONE, site_name=SITE_NAME)
 
@app.route('/kids')
def kids():
    filtered = [p for p in get_products_list() if p['category'] == 'kids']
    return render_template('category.html', products=filtered, category="Балалар",
                           category_en="kids", category_desc="Балаларға арналған қазақ ұлттық кәжекей мен күртеше.",
                           contact=CONTACT_DISPLAY, phone=CONTACT_PHONE, site_name=SITE_NAME)
 
@app.route('/product/<slug>')
def product_detail(slug):
    product = get_product_by_slug(slug)
    if not product:
        abort(404)
    return render_template('product_detail.html', product=product,
                           related_products=get_related(product),
                           contact=CONTACT_DISPLAY, phone=CONTACT_PHONE,
                           site_name=SITE_NAME, base_url=BASE_URL)
 
@app.route('/product/<int:product_id>')
def product_detail_old(product_id):
    products = load_products()
    product = products.get(str(product_id))
    if not product:
        abort(404)
    return redirect(f"/product/{product['slug']}", code=301)
 
@app.route('/about')
def about():
    return render_template('about.html', contact=CONTACT_DISPLAY,
                           phone=CONTACT_PHONE, site_name=SITE_NAME)
 
@app.route('/contact')
def contact():
    return render_template('contact.html', contact=CONTACT_DISPLAY,
                           phone=CONTACT_PHONE, site_name=SITE_NAME)
 
@app.route('/sitemap.xml')
def sitemap():
    pages = ['/', '/women', '/men', '/kids', '/about', '/contact']
    product_urls = [f"/product/{p['slug']}" for p in get_products_list()]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in pages + product_urls:
        xml += f'  <url><loc>{BASE_URL}{url}</loc></url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')
 
# ============================================================
#  АДМИН МАРШРУТТАРЫ
# ============================================================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = ''
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin')
        error = 'Қате пароль!'
    return render_template('admin.html', page='login', error=error)
 
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/admin/login')
 
@app.route('/admin')
@admin_required
def admin_dashboard():
    products = get_products_list()
    return render_template('admin.html', page='dashboard', products=products,
                           total=len(products),
                           men_count=sum(1 for p in products if p['category']=='men'),
                           women_count=sum(1 for p in products if p['category']=='women'),
                           kids_count=sum(1 for p in products if p['category']=='kids'))
 
@app.route('/admin/product/new', methods=['GET', 'POST'])
@admin_required
def admin_new_product():
    if request.method == 'POST':
        products  = load_products()
        new_id    = max((int(k) for k in products.keys()), default=0) + 1
        title     = request.form.get('title', '').strip()
        price_num = int(request.form.get('price_num') or 16000)
        slug      = request.form.get('slug', '').strip() or slugify(title) or f'product-{new_id}'
        if slug in {p['slug'] for p in products.values()}:
            slug = f"{slug}-{new_id}"
        sizes = [s.strip() for s in request.form.get('sizes', '').split(',') if s.strip()]
        products[str(new_id)] = {
            "id": new_id, "slug": slug, "title": title,
            "price": format_price(price_num), "price_num": price_num,
            "image": request.form.get('image', f'dress{new_id}.1.png').strip(),
            "detail_image": request.form.get('detail_image', f'dress{new_id}.jpg').strip(),
            "theme": request.form.get('theme', 'theme-1'),
            "category": request.form.get('category', 'men'),
            "description": request.form.get('description', '').strip(),
            "material": request.form.get('material', '').strip(),
            "color": request.form.get('color', '').strip(),
            "sizes": sizes,
        }
        save_products(products)
        return redirect('/admin')
    return render_template('admin.html', page='form', product=None, action='new')
 
@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    products = load_products()
    key = str(product_id)
    if key not in products:
        abort(404)
    if request.method == 'POST':
        price_num = int(request.form.get('price_num') or 16000)
        slug      = request.form.get('slug', '').strip() or slugify(request.form.get('title', ''))
        sizes     = [s.strip() for s in request.form.get('sizes', '').split(',') if s.strip()]
        products[key].update({
            "slug": slug,
            "title": request.form.get('title', '').strip(),
            "price": format_price(price_num), "price_num": price_num,
            "image": request.form.get('image', '').strip(),
            "detail_image": request.form.get('detail_image', '').strip(),
            "theme": request.form.get('theme', 'theme-1'),
            "category": request.form.get('category', 'men'),
            "description": request.form.get('description', '').strip(),
            "material": request.form.get('material', '').strip(),
            "color": request.form.get('color', '').strip(),
            "sizes": sizes,
        })
        save_products(products)
        return redirect('/admin')
    product = products[key]
    product['sizes_str'] = ', '.join(product.get('sizes', []))
    return render_template('admin.html', page='form', product=product, action='edit')
 
@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    products = load_products()
    products.pop(str(product_id), None)
    save_products(products)
    return redirect('/admin')
 
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', site_name=SITE_NAME), 404
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
