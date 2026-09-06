import os
import hmac
import hashlib
import streamlit as st
import razorpay

from dotenv import load_dotenv
from streamlit.components.v1 import html


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("rzp_test_TYdM4HYUpyK0Iv")
RAZORPAY_KEY_SECRET = os.getenv("VMAN5V7ruN1TFCGAfIsw0aI9")

PRICE_PER_MEMBER = 50


if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    st.error(
        "Razorpay keys are missing. "
        "Please check your .env file."
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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Team Payment",
    page_icon="💳",
    layout="centered"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        max-width: 700px;
        margin: auto;
    }

    .payment-card {
        background: white;
        padding: 30px;
        border-radius: 18px;
        box-shadow: 0 10px 35px rgba(0,0,0,0.10);
        margin-top: 30px;
    }

    .test-mode {
        background: #fff3cd;
        color: #856404;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 20px;
        font-weight: 600;
    }

    .price-box {
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
    '<div class="test-mode">'
    '⚠️ Razorpay TEST MODE'
    '</div>',
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
# CALCULATE
# ============================================================

total_rupees = (
    members * PRICE_PER_MEMBER
)

total_paise = (
    total_rupees * 100
)


# ============================================================
# SUMMARY
# ============================================================

st.markdown(
    f"""
    <div class="price-box">

        <p>
            <b>Members:</b> {members}
        </p>

        <p>
            <b>Price per member:</b> ₹{PRICE_PER_MEMBER}
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
# CREATE RAZORPAY ORDER
# ============================================================

if st.button(
    f"Pay ₹{total_rupees}",
    type="primary",
    use_container_width=True
):

    try:

        # IMPORTANT:
        # Calculate amount on the server.
        # Do not trust amount from frontend.

        amount_paise = (
            int(members)
            * PRICE_PER_MEMBER
            * 100
        )


        order_data = {

            "amount": amount_paise,

            "currency": "INR",

            "receipt":
                f"team_{int(members)}_{os.urandom(4).hex()}",

            "notes": {

                "members":
                    str(members),

                "price_per_member":
                    str(PRICE_PER_MEMBER)

            }

        }


        order = client.order.create(
            data=order_data
        )


        st.session_state["order_id"] = order["id"]

        st.session_state["order_amount"] = order["amount"]

        st.session_state["members"] = int(members)

        st.session_state["payment_started"] = True


        st.rerun()


    except Exception as e:

        st.error(
            f"Unable to create Razorpay order: {e}"
        )


# ============================================================
# RAZORPAY CHECKOUT
# ============================================================

if st.session_state.get(
    "payment_started",
    False
):

    order_id = st.session_state["order_id"]

    order_amount = st.session_state["order_amount"]

    member_count = st.session_state["members"]


    # HTML + JavaScript executed in browser
    checkout_html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>

    </head>

    <body>

        <script>

            const options = {{

                key: "{RAZORPAY_KEY_ID}",

                amount: {order_amount},

                currency: "INR",

                name: "My Team",

                description:
                    "{member_count} team member(s)",

                order_id: "{order_id}",

                handler: function(response) {{

                    const data = {{

                        razorpay_order_id:
                            response.razorpay_order_id,

                        razorpay_payment_id:
                            response.razorpay_payment_id,

                        razorpay_signature:
                            response.razorpay_signature

                    }};

                    // Send result to Streamlit
                    window.parent.postMessage(
                        {{
                            type: "razorpay_payment_success",
                            data: data
                        }},
                        "*"
                    );

                }},

                modal: {{

                    ondismiss: function() {{

                        window.parent.postMessage(
                            {{
                                type: "razorpay_payment_closed"
                            }},
                            "*"
                        );

                    }}

                }},

                theme: {{

                    color: "#3399cc"

                }}

            }};


            const razorpay =
                new Razorpay(options);


            razorpay.on(
                "payment.failed",
                function(response) {{

                    window.parent.postMessage(
                        {{
                            type: "razorpay_payment_failed",

                            data: {{
                                code:
                                    response.error.code,

                                description:
                                    response.error.description

                            }}
                        }},
                        "*"
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
        height=100,
        scrolling=False
    )


    st.info(
        "Razorpay Checkout is ready."
    )


# ============================================================
# PAYMENT VERIFICATION FUNCTION
# ============================================================

def verify_payment(
    order_id,
    payment_id,
    signature
):

    message = (
        order_id
        + "|"
        + payment_id
    )


    generated_signature = hmac.new(

        RAZORPAY_KEY_SECRET.encode(),

        message.encode(),

        hashlib.sha256

    ).hexdigest()


    return hmac.compare_digest(
        generated_signature,
        signature
    )


# ============================================================
# DEBUG INFORMATION
# ============================================================

with st.expander("Developer Information"):

    st.write(
        "Razorpay Key ID:",
        RAZORPAY_KEY_ID
    )

    if st.session_state.get("order_id"):

        st.write(
            "Order ID:",
            st.session_state["order_id"]
        )

    st.write(
        "Price per member:",
        f"₹{PRICE_PER_MEMBER}"
    )

    st.write(
        "Current members:",
        members
    )

    st.write(
        "Current amount:",
        f"₹{total_rupees}"
    )
