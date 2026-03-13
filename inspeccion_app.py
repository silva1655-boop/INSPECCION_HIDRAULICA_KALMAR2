"""Streamlit app for hydraulic inspection forms.

This app displays reference images for hydraulic systems and allows the user to
evaluate the condition of hydraulic hoses, terminals and lift cylinders. For
each component the inspector can choose a status (Bueno, Regular, Malo), add
observations and optionally capture a photo directly from their device's
camera. When the form is submitted, the responses are appended to an Excel
spreadsheet stored alongside this script. Captured photos are saved in an
``evidence`` directory and their file names are recorded in the Excel file.

To run the application locally, install Streamlit (``pip install streamlit``)
and run ``streamlit run streamlit_inspeccion_app.py`` in a terminal. The app
will open in a web browser.  The Excel file ``registro_inspecciones.xlsx``
will be created or updated in the same directory when submissions are saved.
"""

import os
import datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import streamlit as st


def load_reference_images() -> List[Dict[str, Any]]:
    """Return a list of dictionaries describing the reference images.

    Each dictionary contains a title and the path to the image file. The images
    shipped with this project depict different views of a hydraulic system and
    are stored in the same directory as this script.
    """
    base_dir = Path(__file__).resolve().parent
    images_info = [
        {
            "title": "Conjunto de flexibles y componentes (Vista 1)",
            "path": base_dir / "5835788d-17c6-4868-b511-9f1d8c6ca27c.png",
        },
        {
            "title": "Conjunto de flexibles y componentes (Vista 2)",
            "path": base_dir / "76164296-abbd-4216-b789-a85bebff607f.png",
        },
        {
            "title": "Conjunto de flexibles y componentes (Vista 3)",
            "path": base_dir / "7b28b868-8f14-4cc6-a84b-2fef321e2a55.png",
        },
        {
            "title": "Conjunto de flexibles y componentes (Vista 4)",
            "path": base_dir / "10d3488f-5cf0-42c4-8bb7-004b29b53513.png",
        },
        {
            "title": "Detalle de flexibles y válvulas (Vista 5)",
            "path": base_dir / "39ded217-dd8e-4355-9395-a9f3ffd9ef3c.png",
        },
        {
            "title": "Detalle de componentes (Vista 6)",
            "path": base_dir / "aa8a9f13-1bb5-4b81-a2ac-db56dfa06993.png",
        },
        {
            "title": "Detalle de sistema hidráulico (Vista 7)",
            "path": base_dir / "a3adf982-8286-4f0b-b58f-57ce85ae84cf.png",
        },
    ]
    return images_info


def initialize_excel(excel_path: Path, columns: List[str]) -> pd.DataFrame:
    """Ensure the Excel file exists with the given columns and return its DataFrame.

    If the Excel file does not exist, this function creates an empty DataFrame
    with the specified columns and saves it. Otherwise, it reads the existing
    file. The returned DataFrame is used to append new entries.
    """
    if excel_path.exists():
        return pd.read_excel(excel_path)
    df = pd.DataFrame(columns=columns)
    df.to_excel(excel_path, index=False)
    return df


def append_to_excel(df: pd.DataFrame, row: Dict[str, Any], excel_path: Path) -> None:
    """Append a single row to the Excel file stored at excel_path.

    The existing DataFrame is updated with the new row and saved back to
    ``excel_path``. If the file does not exist, it is created.
    """
    df = df.append(row, ignore_index=True)
    df.to_excel(excel_path, index=False)


def save_uploaded_image(uploaded_bytes: bytes, output_dir: Path, prefix: str) -> str:
    """Save an uploaded or captured image to the output directory and return its filename.

    Parameters
    ----------
    uploaded_bytes: bytes
        The image data as bytes.
    output_dir: Path
        Directory where the image will be stored.
    prefix: str
        Prefix for the filename; typically includes the component index or name.

    Returns
    -------
    str
        The filename of the saved image (not including the directory).
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")
    filename = f"{prefix}_{timestamp}.png"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / filename
    with open(out_path, "wb") as f:
        f.write(uploaded_bytes)
    return filename


def main() -> None:
    """Run the Streamlit inspection form app."""
    st.set_page_config(page_title="Formulario de inspección hidráulica", layout="centered")
    st.title("Formulario de inspección de sistemas hidráulicos")
    st.write(
        "Revise visualmente los componentes hidráulicos que se muestran a continuación. "
        "Para cada componente, seleccione el estado (Bueno, Regular o Malo), escriba "
        "comentarios y capture una foto si observa daños o fugas."
    )

    images_info = load_reference_images()

    # Define columns for Excel file. For each component we store status,
    # observations and filename of captured photo
    base_columns = ["fecha", "inspector", "equipo"]
    for i, info in enumerate(images_info, start=1):
        comp_prefix = f"comp{i}"
        base_columns.extend([
            f"{comp_prefix}_estado",
            f"{comp_prefix}_observaciones",
            f"{comp_prefix}_foto",
        ])

    excel_path = Path("registro_inspecciones.xlsx")
    df_existing = initialize_excel(excel_path, base_columns)

    # Evidence directory for captured images
    evidence_dir = Path("evidence")

    # Create the form
    with st.form("inspection_form"):
        fecha = st.date_input("Fecha de inspección", value=datetime.date.today())
        inspector = st.text_input("Nombre del inspector")
        equipo = st.text_input("Equipo/Número de serie")

        # Prepare to collect responses
        responses = {}

        for idx, info in enumerate(images_info, start=1):
            st.subheader(info["title"])
            # Display the reference image
            st.image(str(info["path"]), use_column_width=True)
            # Status radio selection
            estado = st.radio(
                f"Estado del elemento {idx}",
                ["Bueno", "Regular", "Malo"],
                index=0,
                key=f"estado_{idx}",
            )
            observaciones = st.text_area(
                f"Observaciones / Fugas detectadas para el elemento {idx}",
                key=f"observaciones_{idx}",
            )
            # Camera input for capturing a photo
            foto = st.camera_input(
                f"Capturar foto de daños (opcional) para el elemento {idx}",
                key=f"foto_{idx}",
            )
            # Store responses in dictionary
            responses[idx] = {
                "estado": estado,
                "observaciones": observaciones,
                "foto_data": foto,
            }

        submitted = st.form_submit_button("Guardar inspección")

    if submitted:
        # Build the row to append
        new_row = {
            "fecha": fecha,
            "inspector": inspector,
            "equipo": equipo,
        }
        for idx in range(1, len(images_info) + 1):
            comp_prefix = f"comp{idx}"
            estado = responses[idx]["estado"]
            observaciones = responses[idx]["observaciones"]
            foto_widget = responses[idx]["foto_data"]
            # Save photo if provided
            foto_filename = ""
            if foto_widget is not None:
                # `foto_widget` is a Streamlit UploadedFile; read as bytes
                image_bytes = foto_widget.getvalue()
                foto_filename = save_uploaded_image(image_bytes, evidence_dir, comp_prefix)
            new_row[f"{comp_prefix}_estado"] = estado
            new_row[f"{comp_prefix}_observaciones"] = observaciones
            new_row[f"{comp_prefix}_foto"] = foto_filename
        # Append to Excel
        append_to_excel(df_existing, new_row, excel_path)
        st.success("¡Inspección guardada correctamente!")


if __name__ == "__main__":
    main()
