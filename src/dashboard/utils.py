import pandas as pd
import plotly.express as px


def format_currency(value):
    """
    Formata valores para o padrão brasilero.
    """
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_numbers(value):
    """
    Formata números para o padrão brasileiro.
    """
    return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def plot_bar(data: pd.DataFrame, 
             title: str, 
             x: str, 
             y: str = None,
             text_auto: bool = False,
             color: str = None, 
             xlabel: str = None, 
             ylabel: str = None, 
             histnorm: str = None):
    """
    Cria um gráfico de barras utilizando Plotly Express
    Funciona tanto para contagem quanto para valores específicos
    """
    fig = px.histogram(
        data,
        x=x,
        y=y,
        text_auto=text_auto,
        color=color,
        title=title,
        histnorm=histnorm,
        color_discrete_sequence=["#130a24", 
                                 "#3a3548", 
                                 "#666170", 
                                 "#95929a",
                                 "#c6c6c6", 
                                 "#d1a8a7", 
                                 "#d68889", 
                                 "#d7666c", 
                                 "#de425b"]
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)',
        xaxis_title=xlabel or x,
        yaxis_title=ylabel or ('Proporção (%)' if histnorm == 'percent' else 'Contagem'),
        bargap=0.1
    )
    
    return fig

def plot_pie(data: pd.DataFrame, 
             names: str, 
             values: str = None,
             title: str = ""):
    """
    Cria um gráfico de pizza utilizando Plotly Express
    Pode ser usado para contagem (sem valores) ou valores agregados.
    """
    fig = px.pie(
        data,
        names=names,
        values=values,
        title=title,
        hole=0.65,
        color_discrete_sequence=[
            "#130a24", "#3a3548", "#666170", "#95929a", "#c6c6c6",
            "#d1a8a7", "#d68889", "#d7666c", "#de425b"
        ]
    )
    
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)')
    
    return fig