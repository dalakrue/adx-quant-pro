import streamlit as st


def main():
    try:
        st.set_page_config(
            page_title="ADX Quant Pro",
            page_icon="⚡",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        pass

    try:
        from core.app_shell import run_app
        run_app()

    except ImportError as e:
        st.error("Import error. Check your core/app_shell.py file.")
        st.code(str(e))

    except Exception as e:
        st.error("App crashed, but main file is working.")
        st.code(str(e))


if __name__ == "__main__":
    main()