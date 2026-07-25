"""Inventory page — product table with edit & delete actions."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import requests
import streamlit as st

from api_client import API_BASE_URL, create_product, delete_product, fetch_products, update_product


def products_to_dataframe(products: list[dict[str, Any]]) -> pd.DataFrame:
    if not products:
        return pd.DataFrame(
            columns=[
                "ID",
                "Name",
                "SKU",
                "Price",
                "Stock",
                "Active",
                "Description",
            ]
        )

    rows = [
        {
            "ID": p["id"],
            "Name": p["name"],
            "SKU": p["sku"],
            "Price": float(p["price"]),
            "Stock": p["stock_quantity"],
            "Active": p["is_active"],
            "Description": p.get("description") or "",
        }
        for p in products
    ]
    return pd.DataFrame(rows)


def _parse_price(value: str) -> Decimal:
    cleaned = value.strip().replace("$", "").replace(",", "")
    price = Decimal(cleaned)
    if price <= 0:
        raise ValueError("Price must be greater than 0")
    return price.quantize(Decimal("0.01"))


def _flash(level: str, message: str) -> None:
    st.session_state["flash"] = {"level": level, "message": message}


def _show_flash() -> None:
    flash = st.session_state.pop("flash", None)
    if not flash:
        return
    level = flash.get("level", "info")
    message = flash.get("message", "")
    if level == "success":
        st.success(message)
        st.toast(message, icon="✅")
    elif level == "error":
        st.error(message)
        st.toast(message, icon="⚠️")
    else:
        st.info(message)


def _set_edit_product(product_id: int) -> None:
    st.session_state["edit_product_id"] = product_id


def _do_delete_product(product_id: int, hard_delete: bool) -> None:
    try:
        delete_product(product_id, soft=not hard_delete)
    except requests.RequestException as exc:
        _flash("error", f"Failed to delete product #{product_id}: {exc}")
        return

    if hard_delete:
        _flash("success", f"Product #{product_id} permanently deleted.")
    else:
        _flash(
            "success",
            f"Product #{product_id} deactivated (soft delete). "
            "Turn off “Active products only” to see inactive items.",
        )
    st.session_state.pop("edit_product_id", None)


@st.dialog("Edit product")
def edit_product_dialog(product: dict[str, Any]) -> None:
    st.caption(f"Editing product **#{product['id']}**")

    with st.form("edit_product_form"):
        name = st.text_input("Name", value=product["name"], max_chars=150)
        sku = st.text_input("SKU", value=product["sku"], max_chars=50)
        price = st.text_input("Price", value=str(product["price"]))
        stock_quantity = st.number_input(
            "Stock quantity",
            min_value=0,
            step=1,
            value=int(product["stock_quantity"]),
        )
        description = st.text_area(
            "Description",
            value=product.get("description") or "",
            height=100,
        )
        is_active = st.checkbox("Active", value=bool(product["is_active"]))
        submitted = st.form_submit_button(
            "Save changes", type="primary", use_container_width=True
        )

    if not submitted:
        return

    if not name.strip() or not sku.strip():
        st.error("Name and SKU are required.")
        return

    try:
        price_value = _parse_price(price)
    except (InvalidOperation, ValueError) as exc:
        st.error(f"Invalid price: {exc}")
        return

    payload = {
        "name": name.strip(),
        "sku": sku.strip(),
        "price": str(price_value),
        "stock_quantity": int(stock_quantity),
        "description": description.strip() or None,
        "is_active": is_active,
    }

    try:
        update_product(product["id"], payload)
    except requests.RequestException as exc:
        st.error(f"Failed to update product: {exc}")
        return

    _flash("success", f"Product #{product['id']} updated.")
    st.session_state.pop("edit_product_id", None)
    st.rerun()


@st.dialog("Add product")
def create_product_dialog() -> None:
    st.caption("Add a new product to the inventory")

    with st.form("create_product_form"):
        name = st.text_input("Name", max_chars=150)
        sku = st.text_input("SKU", max_chars=50)
        price = st.text_input("Price")
        stock_quantity = st.number_input(
            "Stock quantity",
            min_value=0,
            step=1,
            value=0,
        )
        description = st.text_area(
            "Description",
            height=100,
        )
        is_active = st.checkbox("Active", value=True)
        submitted = st.form_submit_button(
            "Add product", type="primary", use_container_width=True
        )

    if not submitted:
        return

    if not name.strip() or not sku.strip():
        st.error("Name and SKU are required.")
        return

    try:
        price_value = _parse_price(price)
    except (InvalidOperation, ValueError) as exc:
        st.error(f"Invalid price: {exc}")
        return

    payload = {
        "name": name.strip(),
        "sku": sku.strip(),
        "price": str(price_value),
        "stock_quantity": int(stock_quantity),
        "description": description.strip() or None,
        "is_active": is_active,
    }

    try:
        product = create_product(payload)
    except requests.RequestException as exc:
        st.error(f"Failed to create product: {exc}")
        return

    _flash("success", f"Product #{product['id']} created.")
    st.rerun()


def render_actions(products: list[dict[str, Any]], hard_delete: bool) -> None:
    st.subheader("Actions")
    delete_hint = "permanently remove" if hard_delete else "deactivate (soft delete)"
    st.caption(
        f"Use **Edit** to open the update form, or **Delete** to {delete_hint} a product."
    )

    header = st.columns([0.6, 2.2, 1.4, 1.0, 0.8, 0.7, 0.9, 0.9])
    header[0].markdown("**ID**")
    header[1].markdown("**Name**")
    header[2].markdown("**SKU**")
    header[3].markdown("**Price**")
    header[4].markdown("**Stock**")
    header[5].markdown("**Active**")
    header[6].markdown("**Edit**")
    header[7].markdown("**Delete**")

    for product in products:
        cols = st.columns([0.6, 2.2, 1.4, 1.0, 0.8, 0.7, 0.9, 0.9])
        cols[0].write(product["id"])
        cols[1].write(product["name"])
        cols[2].write(product["sku"])
        cols[3].write(f"${float(product['price']):.2f}")
        cols[4].write(product["stock_quantity"])
        cols[5].write("✅" if product["is_active"] else "❌")

        cols[6].button(
            "✏️ Edit",
            key=f"edit_{product['id']}",
            use_container_width=True,
            on_click=_set_edit_product,
            args=(product["id"],),
        )

        cols[7].button(
            "🗑️ Del",
            key=f"delete_{product['id']}",
            use_container_width=True,
            type="primary" if hard_delete else "secondary",
            on_click=_do_delete_product,
            args=(product["id"], hard_delete),
        )


def main() -> None:
    st.title("📦 Product Inventory")
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.markdown("Browse products and use **Edit** / **Delete** actions on each row.")
    with col2:
        if st.button("➕ Add Product", type="primary", use_container_width=True):
            create_product_dialog()

    with st.sidebar:
        st.header("Filters")
        active_only = st.toggle("Active products only", value=True)
        hard_delete = st.toggle(
            "Hard delete",
            value=False,
            help="When enabled, Delete permanently removes the product. "
            "When off (default), Delete deactivates the product (soft delete).",
        )
        st.divider()
        st.caption(f"API: `{API_BASE_URL}`")
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    _show_flash()

    try:
        products = fetch_products(active_only=active_only)
    except requests.ConnectionError:
        st.error(
            f"Cannot reach the API at `{API_BASE_URL}`. "
            "Start the backend with:\n\n"
            "```bash\nuvicorn backend.crud_app.main:app --reload --port 8000\n```"
        )
        return
    except requests.RequestException as exc:
        st.error(f"Failed to load products: {exc}")
        return

    st.subheader("Products")
    df = products_to_dataframe(products)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "Active": st.column_config.CheckboxColumn(disabled=True),
        },
    )
    st.caption(f"{len(products)} product(s)")

    if not products:
        st.info("No products found. Seed the database or create products via the API.")
        return

    st.divider()
    render_actions(products, hard_delete=hard_delete)

    edit_id = st.session_state.get("edit_product_id")
    if edit_id is not None:
        product = next((p for p in products if p["id"] == edit_id), None)
        if product is None:
            st.session_state.pop("edit_product_id", None)
            st.warning(f"Product #{edit_id} is no longer available.")
        else:
            edit_product_dialog(product)


main()
