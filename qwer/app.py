from flask import Flask, render_template, abort, Response, request, redirect, session
from functools import wraps
import os, re, urllib.parse
import cloudinary
import cloudinary.uploader
from supabase import create_client

app = Flask(__name__)
app.secret_key = "kz_admin_secret_2025"

# ── КОНФИГ ──────────────────────────────────────────────────
ADMIN_PASSWORD  = "admin123"
BASE_URL        = "https://ernur1-2.onrender.com"
CONTACT_PHONE   = "77773988869"
CONTACT_DISPLAY = "+7 777 398 8869"
SITE_NAME       = "KZ Ұлттық киімдер дүкені"
SITE_DESC       = "Қазақстанның дәстүрлі ұлттық киімдері. Камзол, шапан, күртеше."

# ── SUPABASE ────────────────────────────────────────────────
supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SECRET_KEY")
)

# ── CLOUDINARY ──────────────────────────────────────────────
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key    = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
    secure     = True
)

# ── JINJA2 ФИЛЬТРІ ──────────────────────────────────────────
@app.template_filter('urlencode')
def urlencode_filter(s):
    return urllib.parse.quote(str(s))

# ── HELPERS ─────────────────────────────────────────────────
KK_MAP = str.maketrans('ұүқғңөіәһ', 'uukgnoiah')
def slugify(text):
    text = text.lower().strip().translate(KK_MAP)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:60]

def format_price(n):
    return f"{int(n):,}".replace(',', ' ') + ' ₸'

def get_products():
    res = supabase.table('products').select('*').order('id').execute()
    return res.data or []

def get_product_by_slug(slug):
    res = supabase.table('products').select('*').eq('slug', slug).execute()
    return res.data[0] if res.data else None

def get_related(product, count=3):
    res = supabase.table('products').select('*')\
        .eq('category', product['category'])\
        .neq('id', product['id'])\
        .limit(count).execute()
    return res.data or []

def parse_sizes(product):
    sizes = product.get('sizes', '')
    if isinstance(sizes, list):
        return sizes
    if sizes:
        return [s.strip() for s in sizes.split(',') if s.strip()]
    return []

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated

# ── САЙТ МАРШРУТТАРЫ ────────────────────────────────────────
@app.route('/')
def index():
    products = get_products()
    for p in products:
        p['sizes'] = parse_sizes(p)
    return render_template('index.html', products=products,
                           contact=CONTACT_DISPLAY, phone=CONTACT_PHONE,
                           site_name=SITE_NAME, site_description=SITE_DESC)

@app.route('/women')
def women():
    res = supabase.table('products').select('*').eq('category', 'women').execute()
    products = res.data or []
    return render_template('category.html', products=products, category="Қыздар",
                           category_en="women",
                           category_desc="Қыздарға арналған қазақ ұлттық камзол мен күртеше.",
                           contact=CONTACT_DISPLAY, phone=CONTACT_PHONE, site_name=SITE_NAME)

@app.route('/men')
def men():
    res = supabase.table('products').select('*').eq('category', 'men').execute()
    products = res.data or []
    return render_template('category.html', products=products, category="Ұлдар",
                           category_en="men",
                           category_desc="Ерлерге арналған ұлттық шапан мен камзол.",
                           contact=CONTACT_DISPLAY, phone=CONTACT_PHONE, site_name=SITE_NAME)

@app.route('/kids')
def kids():
    res = supabase.table('products').select('*').eq('category', 'kids').execute()
    products = res.data or []
    return render_template('category.html', products=products, category="Балалар",
                           category_en="kids",
                           category_desc="Балаларға арналған қазақ ұлттық кәжекей мен күртеше.",
                           contact=CONTACT_DISPLAY, phone=CONTACT_PHONE, site_name=SITE_NAME)

@app.route('/product/<slug>')
def product_detail(slug):
    product = get_product_by_slug(slug)
    if not product:
        abort(404)
    product['sizes'] = parse_sizes(product)
    related = get_related(product)
    return render_template('product_detail.html', product=product,
                           related_products=related,
                           contact=CONTACT_DISPLAY, phone=CONTACT_PHONE,
                           site_name=SITE_NAME, base_url=BASE_URL)

@app.route('/about')
def about():
    return render_template('about.html', contact=CONTACT_DISPLAY,
                           phone=CONTACT_PHONE, site_name=SITE_NAME)

@app.route('/contact')
def contact_page():
    return render_template('contact.html', contact=CONTACT_DISPLAY,
                           phone=CONTACT_PHONE, site_name=SITE_NAME)

@app.route('/sitemap.xml')
def sitemap():
    pages = ['/', '/women', '/men', '/kids', '/about', '/contact']
    products = get_products()
    product_urls = [f"/product/{p['slug']}" for p in products]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in pages + product_urls:
        xml += f'  <url><loc>{BASE_URL}{url}</loc></url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')

# ── АДМИН МАРШРУТТАРЫ ───────────────────────────────────────
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
    session.clear()
    return redirect('/admin/login')

@app.route('/admin')
@admin_required
def admin_dashboard():
    products = get_products()
    return render_template('admin.html', page='dashboard', products=products,
                           total=len(products),
                           men_count=sum(1 for p in products if p['category'] == 'men'),
                           women_count=sum(1 for p in products if p['category'] == 'women'),
                           kids_count=sum(1 for p in products if p['category'] == 'kids'))

@app.route('/admin/product/new', methods=['GET', 'POST'])
@admin_required
def admin_new():
    error = ''
    if request.method == 'POST':
        try:
            title     = request.form.get('title', '').strip()
            price_num = int(request.form.get('price_num') or 16000)
            slug      = request.form.get('slug', '').strip() or slugify(title)
            sizes     = request.form.get('sizes', '').strip()
            category  = request.form.get('category', 'men')
            theme     = request.form.get('theme', 'theme-1')

            # Cloudinary-ге сурет жүктеу
            image_url        = ''
            detail_image_url = ''

            file1 = request.files.get('image_file')
            file2 = request.files.get('detail_image_file')

            if file1 and file1.filename:
                res1 = cloudinary.uploader.upload(file1, folder='kz-shop/thumbs')
                image_url = res1['secure_url']

            if file2 and file2.filename:
                res2 = cloudinary.uploader.upload(file2, folder='kz-shop/detail')
                detail_image_url = res2['secure_url']

            # Supabase-ке жазу
            supabase.table('products').insert({
                'slug':         slug,
                'title':        title,
                'price':        format_price(price_num),
                'price_num':    price_num,
                'image':        image_url,
                'detail_image': detail_image_url,
                'theme':        theme,
                'category':     category,
                'description':  request.form.get('description', '').strip(),
                'material':     request.form.get('material', '').strip(),
                'color':        request.form.get('color', '').strip(),
                'sizes':        sizes,
            }).execute()
            return redirect('/admin')
        except Exception as e:
            error = str(e)
    return render_template('admin.html', page='form', product=None, action='new', error=error)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit(product_id):
    res = supabase.table('products').select('*').eq('id', product_id).execute()
    if not res.data:
        abort(404)
    product = res.data[0]
    error = ''

    if request.method == 'POST':
        try:
            title     = request.form.get('title', '').strip()
            price_num = int(request.form.get('price_num') or 16000)
            slug      = request.form.get('slug', '').strip() or slugify(title)
            sizes     = request.form.get('sizes', '').strip()

            image_url        = product.get('image', '')
            detail_image_url = product.get('detail_image', '')

            file1 = request.files.get('image_file')
            file2 = request.files.get('detail_image_file')

            if file1 and file1.filename:
                res1 = cloudinary.uploader.upload(file1, folder='kz-shop/thumbs')
                image_url = res1['secure_url']

            if file2 and file2.filename:
                res2 = cloudinary.uploader.upload(file2, folder='kz-shop/detail')
                detail_image_url = res2['secure_url']

            supabase.table('products').update({
                'slug':         slug,
                'title':        title,
                'price':        format_price(price_num),
                'price_num':    price_num,
                'image':        image_url,
                'detail_image': detail_image_url,
                'theme':        request.form.get('theme', 'theme-1'),
                'category':     request.form.get('category', 'men'),
                'description':  request.form.get('description', '').strip(),
                'material':     request.form.get('material', '').strip(),
                'color':        request.form.get('color', '').strip(),
                'sizes':        sizes,
            }).eq('id', product_id).execute()
            return redirect('/admin')
        except Exception as e:
            error = str(e)

    product['sizes_str'] = product.get('sizes', '')
    return render_template('admin.html', page='form', product=product,
                           action='edit', error=error)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete(product_id):
    supabase.table('products').delete().eq('id', product_id).execute()
    return redirect('/admin')

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', site_name=SITE_NAME), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
