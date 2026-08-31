import numpy as np
import pandas as pd
import altair as alt
import os
import json
from io import StringIO
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

def load_preprocess_data():

  apk_data = pd.read_parquet("datasets/apk_data.parquet")

  return apk_data

def load_permissions_data(apk_data):
  root_dir = os.path.join("datasets", "dataset_permisos", "apks")
  for dir in os.listdir(root_dir):
    permisos_dir = os.path.join(root_dir, dir, "permisos")
    if os.path.isdir(permisos_dir):
      for file in os.listdir(permisos_dir):
        if file.endswith("perm_en.json"):
          with open(os.path.join(permisos_dir, file), "r") as f:
            apk_data.loc[apk_data["App Id"] == dir, "permissions"] = f.read()
  return apk_data

def load_privacy_policy_and_service_terms(apk_data):
  root_dir = os.path.join("datasets", "dataset_politica_privacidad_terminos_uso", "apks")
  for dir in os.listdir(root_dir):
    terms_dir = os.path.join(root_dir, dir, "terminos_servicio")
    privacy_policy_dir = os.path.join(root_dir, dir, "politica_privacidad")

    # cargar terminos de servicio
    if os.path.isdir(terms_dir):
      for file in os.listdir(terms_dir):
        if file.endswith("tos_en.txt"):
          with open(os.path.join(terms_dir, file), "r") as f:
            apk_data.loc[apk_data["App Id"] == dir, "terms_service"] = f.read()

    # cargar politica de privacidad
    if os.path.isdir(privacy_policy_dir):
      for file in os.listdir(privacy_policy_dir):
        if file.endswith("pp_en.txt"):
          with open(os.path.join(privacy_policy_dir, file), "r") as f:
            apk_data.loc[apk_data["App Id"] == dir, "privacy_policy"] = f.read()
  return apk_data

def free_paid_apps_chart(apk_data):
  free_paid_apps_data = apk_data.groupby("Free").count()["App Name"]
  app_count = apk_data["App Name"].count()
  #free_paid_apps_df = pd.DataFrame([{"Type": 'Free', "Count": free_paid_apps_data[True]}, {"Type": 'Paid', "Count": free_paid_apps_data[False]}])
  free_paid_apps_df = pd.DataFrame([['Free', (free_paid_apps_data[True] / app_count) * 100], ['Paid', (free_paid_apps_data[False] / app_count) * 100]], columns=["Type", "Percentage"])

  #TODO comentar colores complementarios, tooltip para ver porcentajes, porcentajes con dos decimales
  free_paid_apps_chart = alt.Chart(free_paid_apps_df).mark_arc().encode(
      theta="Percentage",
      color=alt.Color(
          "Type:N",
          scale=alt.Scale(
              domain=["Free", "Paid"], range=["#1ad5e5", "#e52a1a"]
          ),
      ),
      tooltip=[
          alt.Tooltip("Percentage", title="Percentage", format=".2f"),
          alt.Tooltip("Type", title="Type"),
      ],
  ).properties(
     title=alt.Title("Percentage of paid vs free apps", fontSize=20, anchor="middle")
  )

  return free_paid_apps_chart

def calculate_estimated_revenue(apk_data):
    # filtrar aplicaciones de pago y que tengan como divisa dolares americanos (USD)
    apk_paid_data = apk_data[(~apk_data["Free"]) & (apk_data["Currency"] == "USD")]
    #elimino registros que no tengan Minimum Installs, Maximum Installs o price
    apk_paid_data.dropna(subset = ["Minimum Installs", "Maximum Installs", "Price"], inplace = True)
    apk_paid_data["Estimated Revenue"] = ((apk_paid_data["Minimum Installs"] + apk_paid_data["Maximum Installs"]) * apk_paid_data["Price"]) / 2
    #borro currency, ya que todos los datos son de USD, y free ya que siempre sera false
    apk_paid_data.drop(["Currency", "Free"], axis=1, inplace = True)

    # para obtener el revenue en millones, para una mejor escala
    apk_paid_data['Revenue (USD millions)'] = apk_paid_data['Estimated Revenue'] / (10 ** 6)


    return apk_paid_data

def get_categories(apk_paid_data):
    return apk_paid_data["Category"].sort_values(ascending = True).unique()

def get_developers(apk_paid_data):
    return apk_paid_data["Developer Id"].unique()

def most_revenue_chart(apk_paid_data, category = None, developer = None):
    most_revenue_apps = apk_paid_data.sort_values("Revenue (USD millions)", ascending=False)

    title = "Revenue by apps in USD"

    revenue_field = "Revenue (USD millions)"
    revenue_title = "Revenue (USD millions)"

    if category is not None:
        most_revenue_apps = most_revenue_apps[most_revenue_apps["Category"] == category]
        title = f"{title} for category {category}"

    if developer is not None:
        most_revenue_apps = most_revenue_apps[most_revenue_apps["Developer Id"] == developer]
        title = f"{title} {"for" if category is None else "and"} developer {developer}"
        revenue_field = "Estimated Revenue"
        revenue_title = "Revenue"

    most_revenue_apps = most_revenue_apps.head(20)
    #TODO comentar grid False
    #TODO filtrar por categoria, developer?
    #TODO input para seleccionar mas de 20?
    #TODO comentar developer usar campo revenue sin escalar
    most_revenue_chart = (
        alt.Chart(most_revenue_apps)
        .mark_bar(
            color="#306998",  # Python Blue
            cornerRadiusEnd=4,
        )
        .encode(
            x=alt.X(
                revenue_field,
                title=revenue_title,
                sort="x",  # Sort by x value descending
                axis=alt.Axis(labelFontSize=18, titleFontSize=22),
            ),
            y=alt.Y("App Name", title="App Name", axis=alt.Axis(labelFontSize=18, titleFontSize=22), sort='-x'),
            tooltip=[
                alt.Tooltip(revenue_field, title=revenue_title),
                alt.Tooltip("App Name", title="App Name"),
            ],
        )
        .properties(
            width=1400, height=850, title=alt.Title(title, fontSize=20, anchor="middle")
        )
        #.configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
        .configure_axis(grid=False)
        .configure_view(strokeWidth=0)
    )

    return most_revenue_chart


def category_revenues_chart(apk_paid_data, operation = 'Sum'):
    revenue_grouped_by_category = apk_paid_data.groupby("Category")["Revenue (USD millions)"]
    if operation == 'Mean':
      revenue_by_category = revenue_grouped_by_category.mean()
      title = "Average revenue by category in USD"
    else:
      revenue_by_category = revenue_grouped_by_category.sum()
      title = "Revenue by category in USD"

    revenue_by_category = revenue_by_category.sort_values(ascending=False)

    total_revenue = revenue_by_category.sum();
    revenue_threshold = (total_revenue * 90) / 100
    index = np.argmax(revenue_by_category.cumsum() > revenue_threshold)
    category_revenues = revenue_by_category[:index + 1]
    category_revenues_df = category_revenues.to_frame().reset_index()

    #TODO comentar orientacion horizontal, ordenar de menor a mayor, pie chart, titulo, tooltip, tamaño del grafico y tamaño de fuente, colores y estilos consistentes entre los bar charts y en general
    category_revenues_chart = (
        alt.Chart(category_revenues_df)
        .mark_bar(
            color="#306998",  # Python Blue
            cornerRadiusEnd=4,
        )
        .encode(
            x=alt.X(
                "Revenue (USD millions)",
                title="Revenue (USD millions)",
                axis=alt.Axis(labelFontSize=18, titleFontSize=22),
            ),
            tooltip=[
                alt.Tooltip("Revenue (USD millions)", title="Revenue (USD millions)"),
                alt.Tooltip("Category", title="Category"),
            ],
            y=alt.Y("Category", title="Category", axis=alt.Axis(labelFontSize=18, titleFontSize=22), sort='-x'),
        )
        .properties(
            width=1400, height=850, title=alt.Title(title, fontSize=20, anchor="middle")
        )
        .configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
        .configure_view(strokeWidth=0)
    )

    return category_revenues_chart

def revenue_rating_relation_chart(apk_paid_data):
    #TODO Explicar ajustes para mejorar legibilidad cambio de escala 10 **6, Scaled revenue < 150 y mayor que 1 para eliminar el outlier/
    #, reducir tamaño 5000 maximo para chart, mejorar legibilidad, size = 60 para que se vean mejor los puntos, height 400 para que vea mejor, interactive para que se pueda hacer zoom

    revenue_rating_relation_chart = alt.Chart(
        apk_paid_data.loc[(~apk_paid_data["Rating"].isna()) & (apk_paid_data["Revenue (USD millions)"] < 150) & (apk_paid_data["Revenue (USD millions)"] > 1)]
            .sort_values("Estimated Revenue", ascending=False)
    ).mark_point(size=60).encode(
        x=alt.X('Rating:Q', scale=alt.Scale(zero=False)),
        y=alt.Y('Revenue (USD millions):Q', scale=alt.Scale(zero=False)),
    ).properties(
        height=400
    ).interactive()

    return revenue_rating_relation_chart



def revenue_minimum_android_relation_chart(apk_paid_data, operation = 'Sum'):

    revenue_grouped_by_minimum_android= apk_paid_data.groupby("Minimum Android")["Revenue (USD millions)"]
    if operation == 'Mean':
      revenue_by_minimum_android = revenue_grouped_by_minimum_android.mean()
      title = "Average revenue by minimum android version in USD"
      limit = 10 ** -3
    else:
      revenue_by_minimum_android = revenue_grouped_by_minimum_android.sum()
      title = "Revenue by minimum android version in USD"
      limit = 6

    minimum_android_revenues_df = revenue_by_minimum_android.to_frame().reset_index()

    # filtrar categorias sin suficientes ingresos y ordenar
    minimum_android_revenues_df = minimum_android_revenues_df[minimum_android_revenues_df["Revenue (USD millions)"] > limit].sort_values(ascending=False, by = "Revenue (USD millions)")

    #TODO comentar mismo estilo que chart anterior, filtrar categorias sin suficiente revenue
    revenue_minimum_android_relation_chart = (
        alt.Chart(minimum_android_revenues_df)
        .mark_bar(
            color="#306998",  # Python Blue
            cornerRadiusEnd=4,
        )
        .encode(
            x=alt.X(
                "Revenue (USD millions)",
                title="Revenue (USD millions)",
                axis=alt.Axis(labelFontSize=18, titleFontSize=22),
            ),
            tooltip=[
                alt.Tooltip("Revenue (USD millions)", title="Revenue (USD millions)"),
                alt.Tooltip("Minimum Android", title="Minimum Android"),
            ],
            y=alt.Y("Minimum Android", title="Minimum Android", axis=alt.Axis(labelFontSize=18, titleFontSize=22), sort='-x'),
        )
        .properties(
            width=1400, height=850, title=alt.Title(title, fontSize=20, anchor="middle")
        )
        .configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
        .configure_view(strokeWidth=0)
    )

    return revenue_minimum_android_relation_chart


def revenue_by_content_rating(apk_paid_data, operation = "Sum"):
    revenue_grouped_by_content_rating = apk_paid_data.loc[~apk_paid_data["Content Rating"].isna()].groupby("Content Rating")["Revenue (USD millions)"]
    if operation == 'Mean':
      revenue_by_content_rating = revenue_grouped_by_content_rating.mean()
      title = "Average revenue by content rating in USD"
    else:
      revenue_by_content_rating = revenue_grouped_by_content_rating.sum()
      title = "Revenue by content rating in USD"

    revenue_by_content_rating = revenue_by_content_rating.sort_values(ascending=False).to_frame().reset_index()

    content_rating_revenues_chart = (
        alt.Chart(revenue_by_content_rating)
        .mark_bar(
            color="#306998",  # Python Blue
            cornerRadiusEnd=4,
        )
        .encode(
            x=alt.X(
                "Revenue (USD millions)",
                title="Revenue (USD millions)",
                axis=alt.Axis(labelFontSize=18, titleFontSize=22),
            ),
            tooltip=[
                alt.Tooltip("Revenue (USD millions)", title="Revenue (USD millions)"),
                alt.Tooltip("Content Rating", title="Content Rating"),
            ],
            y=alt.Y("Content Rating", title="Content Rating", axis=alt.Axis(labelFontSize=18, titleFontSize=22), sort='-x'),
        )
        .properties(
            width=1400, height=850, title=alt.Title(title, fontSize=20, anchor="middle")
        )
        .configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
        .configure_view(strokeWidth=0)
    )

    return content_rating_revenues_chart

def extract_permissions(value):
      parsed_json = json.loads(value)
      #print(parsed_json[0]["category"])
      permissions = set()
      for value in parsed_json:
        if "category" in value:
            permissions.add(value["category"])
      return permissions

def permission_count(apk_data):
   result = apk_data[~apk_data["permissions"].isna()]['permissions'].apply(extract_permissions)
   permission_counts = result.explode().reset_index(drop = True).value_counts().to_frame().reset_index()

   permissions_chart = (
        alt.Chart(permission_counts)
        .mark_bar(
            color="#306998",  # Python Blue
            cornerRadiusEnd=4,
        )
        .encode(
            x=alt.X("count", title="Count", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
            y=alt.Y(
                "permissions",
                title="Permissions",
                axis=alt.Axis(labelFontSize=18, titleFontSize=22),
                sort="-x"
            ),
            tooltip=[
                alt.Tooltip("permissions", title="Permissions"),
                alt.Tooltip("count", title="Count"),
            ],
        )
        .properties(
            width=1400, height=850, title=alt.Title("Permission count", fontSize=20, anchor="middle")
        )
        .configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
        .configure_view(strokeWidth=0)
   )

   return permissions_chart

def revenue_by_category_and_rating(apk_paid_data):
   revenue_grouped_by_category = apk_paid_data.groupby("Category")["Estimated Revenue"].sum().sort_values(ascending=False)

   # solo seleccionar elementos de las 10 categorias con mas revenue, para que el grafico no este sobrecargado
   categories = revenue_grouped_by_category.index[:10].values
   revenue_data = apk_paid_data[apk_paid_data["Category"].isin(categories)]

   # el chart tiene un limite de 5000 elementos, por lo que uso sample para obtenerlos
   sampled_revenue_data = revenue_data.sample(5000, weights="Estimated Revenue", replace=True, random_state=123)
   #TODO explicar weights=Estimated revenue, se ha escogido por que se intenta maximizar el revenue
   revenue_by_category_and_rating = (
        alt.Chart(sampled_revenue_data)
        .mark_rect(
            color="#306998",  # Python Blue
            cornerRadiusEnd=4,
        )
        .encode(
            x=alt.X("Category", title="Category", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
            y=alt.Y(
                "Content Rating",
                title="Content Rating",
                axis=alt.Axis(labelFontSize=18, titleFontSize=22),
                sort="-x"
            ),
            color="Estimated Revenue",
            tooltip=[
                alt.Tooltip("Category", title="Category"),
                alt.Tooltip("Content Rating", title="Content Rating"),
            ],
        )
        .properties(
             width=800, height=400, title=alt.Title("Revenue by category and content rating", fontSize=20, anchor="middle")
        )
        .configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
        .configure_view(strokeWidth=0)
   )

   return revenue_by_category_and_rating

def get_apps_wordcloud(apk_data, text_type):
  field = "privacy_policy" if text_type == "Privacy policy" else "terms_service"
  return apk_data[~apk_data[field].isna()]["App Name"]

def generate_wordcloud(apk_data, app_name, text_type):
  if app_name is not None:
      apk_data = apk_data[apk_data["App Name"] == app_name]

  field = "privacy_policy" if text_type == "Privacy policy" else "terms_service"
  text = apk_data[~apk_data[field].isna()][field].str.cat(sep=" ")
  stopwords = STOPWORDS.union({"will", "may", "using", "make"})

  if not text:
      return plt
  wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=stopwords).generate(text)

  plt.figure(figsize=(10, 5))
  plt.title(f"{text_type} word cloud {f"for {app_name}" if app_name is not None else ""}")
  plt.imshow(wordcloud, interpolation='bilinear')
  plt.axis('off')
  return plt
