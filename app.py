import streamlit as st
import sys
import os


# ADD SRC FOLDER TO PYTHON PATH
sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "src"
    )
)

from execution_engine import search



# PAGE CONFIG

st.set_page_config(
    page_title="Intelligent Product Discovery",
    page_icon="🛋️",
    layout="wide"
)



# MODERN IKEA-INSPIRED STYLE


st.markdown("""
<style>

/* MAIN BACKGROUND */

.stApp {
    background-color: #f5f5f5;
}


/* MAIN CONTENT */

.block-container {
    max-width: 1100px;
    padding-top: 3rem;
    padding-bottom: 3rem;
}


/* TITLE */

h1 {
    color: #0058a3;
    font-weight: 800;
    text-align: center;
}


/* SUBHEADINGS */

h2, h3 {
    color: #111111;
    font-weight: 700;
}


/* TEXT INPUT */

.stTextInput input {
    background-color: white;
    border-radius: 10px;
    border: 1px solid #dddddd;
    padding: 14px;
    font-size: 16px;
}


/* SEARCH BUTTON */

.stButton button {
    width: 100%;
    background-color: #0058a3;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px;
    font-weight: 600;
    font-size: 16px;
}

.stButton button:hover {
    background-color: #003f75;
    color: white;
}


/* METRIC CARDS */

[data-testid="stMetric"] {
    background-color: white;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
}


/* PRODUCT CARD */

.product-card {
    background-color: white;
    padding: 25px;
    border-radius: 14px;
    margin-bottom: 10px;
    box-shadow: 0px 3px 12px rgba(0,0,0,0.08);
    border-left: 5px solid #0058a3;
}


/* PRODUCT TITLE */

.product-title {
    font-size: 22px;
    font-weight: 700;
    color: #111111;
    margin-bottom: 15px;
}


/* PRODUCT DETAILS */

.product-detail {
    color: #555555;
    font-size: 15px;
    margin-bottom: 8px;
    word-wrap: break-word;
}


/* PRICE */

.price-box {
    background-color: #ffdb00;
    padding: 18px;
    border-radius: 12px;
    text-align: center;
    font-size: 24px;
    font-weight: 800;
    color: #111111;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)



# HEADER


st.title("🛋️ Intelligent Product Discovery")

st.markdown("""
<p style="text-align:center;
          color:#666;
          font-size:18px;
          margin-bottom:30px;">
Discover products using natural language search
</p>
""", unsafe_allow_html=True)



# SEARCH SECTION


search_col, button_col = st.columns([5, 1])


with search_col:

    query = st.text_input(
        "Search for products",
        placeholder=(
            "Try: Scandinavian-style living room furniture "
            "under $500"
        ),
        label_visibility="collapsed"
    )


with button_col:

    search_clicked = st.button(
        "🔍 Search"
    )

# SEARCH


if search_clicked:

    if not query.strip():

        st.warning(
            "Please enter a product search query."
        )

    else:

        with st.spinner(
            "Searching for the best products..."
        ):

            try:

                output = search(query)

                plan = output["plan"]
                results = output["results"]
                evaluation = output["evaluation"]

            except Exception as e:

                st.error(
                    f"An error occurred: {str(e)}"
                )

                st.stop()


        
        # RESULTS HEADER
       
        st.markdown(
            f'<h3 style="margin-top:40px;">'
            f'Results for: "{query}"'
            f'</h3>',
            unsafe_allow_html=True
        )


       
        # SEARCH METRICS
        

        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "Search Method",
                plan.get(
                    "execution_plan",
                    "N/A"
                )
            )


        with col2:

            st.metric(
                "Products Found",
                len(results)
            )


        with col3:

            confidence = evaluation.get(
                "confidence",
                0
            )

            st.metric(
                "Confidence",
                f"{confidence:.0%}"
            )


    
        # QUERY PLAN
        

        with st.expander(
            "⚙️ View Search Details"
        ):

            st.json(plan)



        # PRODUCTS
        

        st.markdown("<br>", unsafe_allow_html=True)


        if not results:

            st.warning(
                "No products found. Try a different search."
            )


        else:

            for product in results:


                
                # PRODUCT DATA
       

                title = product.get(
                    "product_title",
                    "Unknown Product"
                )

                sku = product.get(
                    "sku",
                    "N/A"
                )

                category = product.get(
                    "breadcrumbs",
                    "N/A"
                )

                availability = product.get(
                    "availability",
                    "N/A"
                )

                price = product.get(
                    "product_price",
                    0
                )

                product_url = product.get(
                    "product_url",
                    None
                )


                
                # PRODUCT CARD LAYOUT
               

                card_col1, card_col2 = st.columns(
                    [4, 1]
                )


              
                # PRODUCT DETAILS
                

                with card_col1:

                    product_html = f"""<div class="product-card">
<div class="product-title">{title}</div>

<div class="product-detail">
<b>SKU:</b> {sku}
</div>

<div class="product-detail">
<b>Category:</b> {category}
</div>

<div class="product-detail">
<b>Availability:</b> {availability}
</div>
</div>"""

                    st.markdown(
                        product_html,
                        unsafe_allow_html=True
                    )


                
                # PRICE
     

                with card_col2:

                    price_html = f"""<div class="price-box">
${price}
</div>"""

                    st.markdown(
                        price_html,
                        unsafe_allow_html=True
                    )


              
                    # PRODUCT LINK
                    

                    if product_url:

                        st.link_button(
                            "View Product",
                            product_url,
                            use_container_width=True
                        )


          
                # SPACE BETWEEN PRODUCTS
           

                st.markdown(
                    "<br>",
                    unsafe_allow_html=True
                )