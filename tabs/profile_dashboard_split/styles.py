import streamlit as st


def profile_css():
    st.markdown(
        """
        <style>
        .profile-card {
            background: linear-gradient(135deg, rgba(235,247,255,.96), rgba(245,248,252,.94));
            border: 1px solid rgba(120,170,210,.38);
            border-radius: 20px;
            padding: 16px;
            box-shadow: 0 8px 24px rgba(30, 90, 130, .10);
            margin-bottom: 14px;
            color: #123;
        }

        .mini-title {
            font-size: 14px;
            opacity: .78;
            font-weight: 800;
            margin-bottom: 5px;
        }

        .big-value {
            font-size: 24px;
            font-weight: 900;
            line-height: 1.15;
            word-break: break-word;
        }

        .status-good {
            color: #087f5b;
            font-weight: 900;
        }

        .status-warn {
            color: #b7791f;
            font-weight: 900;
        }

        .status-bad {
            color: #c92a2a;
            font-weight: 900;
        }

        /* Better tab spacing */
        button[data-baseweb="tab"] {
            font-weight: 800;
            padding: 8px 12px;
        }

        /* Better dataframe/readability */
        div[data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
        }

        /* Better button feel */
        div.stButton > button {
            border-radius: 14px;
            font-weight: 800;
            min-height: 42px;
        }

        /* Inputs */
        div[data-baseweb="input"],
        div[data-baseweb="select"] {
            border-radius: 12px;
        }

        /* Mobile mode */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.7rem !important;
                padding-right: 0.7rem !important;
                padding-top: 0.8rem !important;
            }

            .profile-card {
                padding: 10px;
                border-radius: 14px;
                margin-bottom: 10px;
                font-size: 12px;
            }

            .mini-title {
                font-size: 12px;
            }

            .big-value {
                font-size: 18px;
            }

            div[data-testid="stMetricValue"] {
                font-size: 18px;
            }

            div[data-testid="stMetricLabel"] {
                font-size: 11px;
            }

            button[data-baseweb="tab"] {
                font-size: 12px;
                padding: 6px 8px;
            }

            div.stButton > button {
                min-height: 38px;
                font-size: 13px;
            }

            input,
            textarea {
                font-size: 14px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )