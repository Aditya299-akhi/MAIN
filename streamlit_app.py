import os
import hmac
import hashlib
import streamlit as st
import razorpay

from dotenv import load_dotenv
from streamlit.components.v1 import html


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Team Payment",
    page_icon="💳",
    layout="centered"
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# GET RAZORPAY CREDENTIALS
# ============================================================

# Local:
# Reads from .env
#
# Streamlit Cloud:
# Reads from Streamlit Secrets

try:

    RAZORPAY_KEY_ID = st.secrets.get(
        "RAZORPAY_KEY_ID",
        os.getenv("RAZORPAY_KEY_ID")
    )

    RAZORPAY_KEY_SECRET = st.secrets.get(
        "RAZORPAY_KEY_SECRET",
        os.getenv("RAZORPAY_KEY_SECRET")
    )

except Exception:

    RAZORPAY_KEY_ID = os.getenv(
        "RAZORPAY_KEY_ID"
    )

    RAZORPAY_KEY_SECRET = os.getenv(
        "RAZORPAY_KEY_SECRET"
    )


# ============================================================
# CHECK KEYS
# ============================================================

if not RAZORPAY_KEY_ID:

    st.error(
        "RAZORPAY_KEY_ID is missing."
    )

    st.info(
        "For local testing, add it to .env. "
        "For Streamlit Cloud, add it to App Settings → Secrets."
    )

    st.stop()


if not RAZORPAY_KEY_SECRET:

    st.error(
        "RAZORPAY_KEY_SECRET is missing."
    )

    st.info(
        "For local testing, add it to .env. "
        "For Streamlit Cloud, add it to App Settings → Secrets."
    )

    st.stop()


# ============================================================
# RAZORPAY CLIENT
# ============================================================

client = razorpay.Client(
    auth=(
        RAZORPAY_KEY_ID,
        RAZORPAY_KEY_SECRET
    )
)


# ============================================================
# CONSTANTS
# ============================================================

PRICE_PER_MEMBER = 50


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .payment-card {
        background: white;
        padding: 30px;
        border-radius: 18px;
        box-shadow:
            0 10px 35px
            rgba(0, 0, 0, 0.10);
    }

    .test-mode {
        background: #fff3cd;
        color: #856404;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin: 15px 0 25px 0;
        font-weight: bold;
    }

    .summary {
        background: #f5f9ff;
        padding: 20px;
        border-radius: 12px;
        margin-top: 20px;
    }

    .total {
        font-size: 28px;
        font-weight: bold;
        color: #3399cc;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TITLE
# ============================================================

st.title("💳 Team Payment")

st.write(
    "Test Razorpay payment with ₹50 per team member."
)


st.markdown(
    """
    <div class="test-mode">
        ⚠️ RAZORPAY TEST MODE
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# MEMBER INPUT
# ============================================================

members = st.number_input(
    "Number of Team Members",
    min_value=1,
    max_value=1000,
    value=1,
    step=1
)


# ============================================================
# CALCULATE PRICE
# ============================================================

total_rupees = (
    int(members) * PRICE_PER_MEMBER
)

total_paise = (
    total_rupees * 100
)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

st.markdown(
    f"""
    <div class="summary">

        <p>
            <strong>Members:</strong>
            {members}
        </p>

        <p>
            <strong>Price per member:</strong>
            ₹{PRICE_PER_MEMBER}
        </p>

        <hr>

        <p class="total">
            Total: ₹{total_rupees}
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


st.write("")


# ============================================================
# CREATE ORDER
# ============================================================

if st.button(
    f"Pay ₹{total_rupees}",
    type="primary",
    use_container_width=True
):

    try:

        # IMPORTANT:
        # Calculate amount on backend.
        # Never trust amount supplied by browser.

        amount_paise = (
            int(members)
            * PRICE_PER_MEMBER
            * 100
        )


        order_data = {

            "amount":
                amount_paise,

            "currency":
                "INR",

            "receipt":
                f"team_{int(members)}_"
                f"{os.urandom(5).hex()}",

            "notes": {

                "members":
                    str(int(members)),

                "price_per_member":
                    str(PRICE_PER_MEMBER)

            }

        }


        # Create Razorpay order

        order = client.order.create(
            data=order_data
        )


        # Save order information

        st.session_state[
            "order_id"
        ] = order["id"]


        st.session_state[
            "order_amount"
        ] = order["amount"]


        st.session_state[
            "member_count"
        ] = int(members)


        st.session_state[
            "show_checkout"
        ] = True


        st.rerun()


    except Exception as e:

        st.error(
            "Could not create Razorpay order."
        )

        st.code(
            str(e)
        )


# ============================================================
# RAZORPAY CHECKOUT
# ============================================================

if st.session_state.get(
    "show_checkout",
    False
):


    order_id = st.session_state[
        "order_id"
    ]


    order_amount = st.session_state[
        "order_amount"
    ]


    member_count = st.session_state[
        "member_count"
    ]


    # --------------------------------------------------------
    # RAZORPAY CHECKOUT HTML
    # --------------------------------------------------------

    checkout_html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <script
            src="https://checkout.razorpay.com/v1/checkout.js">
        </script>

        <style>

            body {{
                font-family: Arial;
                text-align: center;
                padding: 10px;
            }}

            .info {{
                color: #666;
                font-size: 14px;
            }}

        </style>

    </head>


    <body>

        <p class="info">
            Opening Razorpay Checkout...
        </p>


        <script>

            const options = {{

                key:
                    "{RAZORPAY_KEY_ID}",

                amount:
                    {order_amount},

                currency:
                    "INR",

                name:
                    "My Team",

                description:
                    "{member_count} team member(s)",

                order_id:
                    "{order_id}",


                handler:
                    function(response) {{

                        document.body.innerHTML = `

                            <h3 style="color:green;">
                                ✅ Payment Successful
                            </h3>

                            <p>
                                Payment ID:
                                <br>
                                <strong>
                                    ${{response.razorpay_payment_id}}
                                </strong>
                            </p>

                            <p>
                                Order ID:
                                <br>
                                <strong>
                                    ${{response.razorpay_order_id}}
                                </strong>
                            </p>

                            <p>
                                Payment signature received.
                            </p>

                        `;

                        console.log(
                            "Payment response:",
                            response
                        );

                    }},


                modal: {{

                    ondismiss:
                        function() {{

                            document.body.innerHTML = `

                                <p>
                                    Payment window closed.
                                </p>

                            `;

                        }}

                }},


                theme: {{

                    color:
                        "#3399cc"

                }}

            }};


            const razorpay =
                new Razorpay(options);


            razorpay.on(
                "payment.failed",
                function(response) {{

                    document.body.innerHTML = `

                        <h3 style="color:red;">
                            ❌ Payment Failed
                        </h3>

                        <p>
                            ${{response.error.description}}
                        </p>

                    `;

                    console.error(
                        response.error
                    );

                }}
            );


            razorpay.open();

        </script>

    </body>

    </html>
    """


    html(
        checkout_html,
        height=250,
        scrolling=False
    )


# ============================================================
# DEVELOPER INFORMATION
# ============================================================

with st.expander(
    "🔧 Developer Information"
):

    st.write(
        "Razorpay Key ID:",
        RAZORPAY_KEY_ID
    )


    if st.session_state.get(
        "order_id"
    ):

        st.write(
            "Order ID:",
            st.session_state[
                "order_id"
            ]
        )


    st.write(
        "Members:",
        int(members)
    )


    st.write(
        "Price per member:",
        f"₹{PRICE_PER_MEMBER}"
    )


    st.write(
        "Total:",
        f"₹{total_rupees}"
    )
