#!/usr/bin/env python

# Created by Raul Peralta-Lozada (28/09/17)
import pandas as pd
import numpy as np
import networkx as nx
from networkx.algorithms import bipartite
from sklearn.linear_model import Ridge


def contratos_por_proveedor(df, **kwargs):
    """Por cada unidad compradora calcula el número de contratos por
    por proveedor diferente
    """
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    # Proveedores distintos
    pocs_distintos = monto_por_contrato.groupby(
        'CLAVEUC').PROVEEDOR_CONTRATISTA.nunique()
    pocs_distintos = pocs_distintos.reset_index()
    pocs_distintos = pocs_distintos.rename(
      columns={'PROVEEDOR_CONTRATISTA': 'proveedores_distintos'})
    # procedimientos distintos
    procedimientos_distintos = monto_por_contrato.groupby(
        'CLAVEUC').NUMERO_PROCEDIMIENTO.nunique()
    procedimientos_distintos = procedimientos_distintos.reset_index()
    procedimientos_distintos = procedimientos_distintos.rename(
      columns={'NUMERO_PROCEDIMIENTO': 'conteo_procedimientos'})
    # Numero de contratos
    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).CODIGO_CONTRATO.nunique()
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.rename(
        columns={'CODIGO_CONTRATO': 'conteo_contratos'})
    contratos_total = contratos_total.groupby(
        'CLAVEUC', as_index=False).conteo_contratos.sum()
    df_feature = pd.merge(
        pocs_distintos, contratos_total, on='CLAVEUC', how='inner')
    df_feature = pd.merge(
        df_feature, procedimientos_distintos, on='CLAVEUC', how='inner')
    df_feature = df_feature.assign(
        contratos_por_proveedor=df_feature.conteo_contratos.divide(df_feature.proveedores_distintos)
    )
    df_feature = df_feature.loc[:, ['CLAVEUC', 'contratos_por_proveedor']]
    return df_feature


def porcentaje_procedimientos_por_tipo(df, **kwargs):
    """Por cada unidad compradora calcula el porcentaje
    de procedimientos por tipo"""
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO', 'TIPO_PROCEDIMIENTO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    conteo_tipos = monto_por_contrato.groupby(
        ['CLAVEUC', 'TIPO_PROCEDIMIENTO']
    ).NUMERO_PROCEDIMIENTO.nunique().reset_index()
    conteo_tipos = conteo_tipos.pivot(
        index='CLAVEUC', columns='TIPO_PROCEDIMIENTO',
        values='NUMERO_PROCEDIMIENTO'
    ).fillna(0)
    total_procedimientos = conteo_tipos.sum(axis=1)
    conteo_tipos = conteo_tipos * 100
    conteo_tipos = conteo_tipos.divide(total_procedimientos, axis='index')
    conteo_tipos = conteo_tipos.rename(
        columns={
            col: 'pc_procedimientos_' + col.replace(' ', '_').lower()
            for col in conteo_tipos.columns
        }
    )
    conteo_tipos = conteo_tipos.reset_index()
    conteo_tipos.columns.name = ''
    return conteo_tipos


def porcentaje_monto_tipo_procedimiento(df, **kwargs):
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO', 'TIPO_PROCEDIMIENTO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    monto_tipos = monto_por_contrato.groupby(
        ['CLAVEUC', 'TIPO_PROCEDIMIENTO'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_tipos = monto_tipos.pivot(
        index='CLAVEUC', columns='TIPO_PROCEDIMIENTO',
        values='IMPORTE_PESOS'
    ).fillna(0)
    total_montos = monto_tipos.sum(axis=1)
    monto_tipos = monto_tipos * 100
    monto_tipos = monto_tipos.divide(total_montos, axis='index')
    monto_tipos = monto_tipos.rename(
        columns={
            col: 'pc_monto_' + col.replace(' ', '_').lower()
            for col in monto_tipos.columns
        }
    )
    monto_tipos = monto_tipos.reset_index()
    monto_tipos.columns.name = ''
    return monto_tipos


def importe_promedio_por_contrato(df, **kwargs):
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).CODIGO_CONTRATO.nunique()
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.rename(columns={'CODIGO_CONTRATO': 'conteo_contratos'})
    contratos_total = contratos_total.groupby('CLAVEUC', as_index=False).conteo_contratos.sum()

    monto_uc_contratos = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_uc_contratos = monto_uc_contratos.groupby('CLAVEUC', as_index=False).IMPORTE_PESOS.sum()

    df_feature = pd.merge(monto_uc_contratos, contratos_total, on='CLAVEUC', how='inner')
    df_feature = df_feature.assign(
        monto_contrato_promedio=df_feature.IMPORTE_PESOS.divide(df_feature.conteo_contratos)
    )
    df_feature = df_feature.drop('conteo_contratos', axis=1)
    df_feature = df_feature.rename(columns={'IMPORTE_PESOS': 'monto_total'})
    df_feature = df_feature.loc[:, ['CLAVEUC', 'monto_contrato_promedio']]
    return df_feature


def calcular_IHH_ID_contratos(df, **kwargs):
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    contratos_uc_poc = monto_por_contrato.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA', 'NUMERO_PROCEDIMIENTO'],
    ).CODIGO_CONTRATO.nunique()
    contratos_uc_poc = contratos_uc_poc.reset_index()
    contratos_uc_poc = contratos_uc_poc.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA'], as_index=False
    ).CODIGO_CONTRATO.sum()
    contratos_uc = contratos_uc_poc.groupby(
        'CLAVEUC', as_index=False
    ).CODIGO_CONTRATO.sum()
    contratos_uc = contratos_uc.rename(
        columns={'CODIGO_CONTRATO': 'contratos_por_uc'}
    )
    contratos_uc_poc = pd.merge(
        contratos_uc_poc, contratos_uc, how='left', on='CLAVEUC'
    )
    contratos_uc_poc = contratos_uc_poc.assign(
        Share=(contratos_uc_poc.CODIGO_CONTRATO.divide(contratos_uc_poc.contratos_por_uc) * 100)
    )
    contratos_uc_poc = contratos_uc_poc.assign(
        IHH_contratos=contratos_uc_poc.Share ** 2
    )
    contratos_uc_poc = contratos_uc_poc.drop(
        ['contratos_por_uc', 'Share'], axis=1)
    # IHH por uc
    uc_IHH = contratos_uc_poc.groupby(
        'CLAVEUC', as_index=False).IHH_contratos.sum()
    uc_IHH = uc_IHH.rename(columns={'IHH_contratos': 'IHH_total_contratos'})

    # ID por uc
    contratos_uc_poc = pd.merge(
        contratos_uc_poc, uc_IHH, on='CLAVEUC', how='inner'
    )
    contratos_uc_poc = contratos_uc_poc.assign(
        ID_contratos=(
            contratos_uc_poc.IHH_contratos.divide(contratos_uc_poc.IHH_total_contratos)
        )
    )
    contratos_uc_poc = contratos_uc_poc.assign(
        ID_contratos=(contratos_uc_poc.ID_contratos * 100) ** 2
    )
    uc_ID = contratos_uc_poc.groupby('CLAVEUC', as_index=False).ID_contratos.sum()
    uc_ID = uc_ID.rename(columns={'ID_contratos': 'ID_total_contratos'})
    # final join
    df_feature = pd.merge(uc_IHH, uc_ID, on='CLAVEUC', how='inner')
    return df_feature


def calcular_IHH_ID_monto(df, **kwargs):
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    monto_uc_poc = monto_por_contrato.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_uc = monto_uc_poc.groupby(
        'CLAVEUC', as_index=False
    ).IMPORTE_PESOS.sum()
    monto_uc = monto_uc.rename(columns={'IMPORTE_PESOS': 'monto_por_uc'})
    monto_uc_poc = pd.merge(monto_uc_poc, monto_uc, how='left', on='CLAVEUC')
    monto_uc_poc = monto_uc_poc.assign(
        Share=(monto_uc_poc.IMPORTE_PESOS.divide(monto_uc_poc.monto_por_uc) * 100)
    )
    monto_uc_poc = monto_uc_poc.assign(
        IHH_monto=monto_uc_poc.Share**2
    )
    uc_IHH = monto_uc_poc.groupby(
        'CLAVEUC', as_index=False).IHH_monto.sum()
    uc_IHH = uc_IHH.rename(columns={'IHH_monto': 'IHH_total_monto'})
    # ID por uc
    monto_uc_poc = pd.merge(monto_uc_poc, uc_IHH, on='CLAVEUC', how='inner')
    monto_uc_poc = monto_uc_poc.assign(
        ID_monto=(
            monto_uc_poc.IHH_monto.divide(monto_uc_poc.IHH_total_monto)
        )
    )
    monto_uc_poc = monto_uc_poc.assign(
        ID_monto=(monto_uc_poc.ID_monto * 100) ** 2
    )
    uc_ID = monto_uc_poc.groupby('CLAVEUC', as_index=False).ID_monto.sum()
    uc_ID = uc_ID.rename(columns={'ID_monto': 'ID_total_monto'})
    # final join
    df_feature = pd.merge(uc_IHH, uc_ID, on='CLAVEUC', how='inner')
    return df_feature


def tendencia_adjudicacion_directa(df, **kwargs):
    # df_procs
    def _estimar_pendiente(row):
        y = row.values.reshape(-1, 1)
        x = np.arange(0, y.shape[0]).reshape(-1, 1)
        # model = Ridge(fit_intercept=False)
        model = Ridge(fit_intercept=True)
        model.fit(x, y)
        pendiente = model.coef_.flatten()[0]
        return pendiente
    if df.shape[0] == 0:
        return None
    df = df.copy()
    df = df.assign(
        adjudicacion_directa=df.TIPO_PROCEDIMIENTO == 'ADJUDICACION DIRECTA'
    )
    cols = [
        'CLAVEUC', 'FECHA_INICIO',
        'NUMERO_PROCEDIMIENTO',
        'TIPO_PROCEDIMIENTO',
        'adjudicacion_directa'
    ]
    df = (df.loc[:, cols]
          .drop_duplicates()
          .assign(Year=df.FECHA_INICIO.dt.year)
          .drop('FECHA_INICIO', axis=1)
          .groupby(['CLAVEUC', 'Year', 'adjudicacion_directa'])
          .NUMERO_PROCEDIMIENTO.nunique()
          .reset_index()
          .pivot_table(index=['CLAVEUC', 'Year'],
                       columns=['adjudicacion_directa'],
                       values='NUMERO_PROCEDIMIENTO')
          .fillna(0)
          .reset_index()
          .rename(columns={True: 'num_adj_si',
                           False: 'num_adj_no'}))
    total = df[['num_adj_no', 'num_adj_si']].sum(axis=1)
    df = df.assign(
        pc_adjudicacion=(df.num_adj_si.divide(total) * 100)
    )
    df = (df.pivot(index='CLAVEUC',
                   columns='Year',
                   values='pc_adjudicacion')
          .drop(2017, axis=1)
          .fillna(0))

    df = df.assign(
        tendencia_adj_directa=df.apply(
            _estimar_pendiente, axis=1)
    )
    df = (df.reset_index()
          .loc[:, ['CLAVEUC', 'tendencia_adj_directa']])
    df.columns.name = ''
    return df


# Datos de la tabla participantes

def porcentaje_licitaciones_con_un_participante(df, **kwargs):
    # usa tabla de participantes
    if df.shape[0] == 0:
        return None
    df = df.copy()
    df_feature = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    col_name = 'pc_licitaciones_un_participante'
    tipos_validos = {'LICITACION PUBLICA',
                     'INVITACION A CUANDO MENOS TRES'}
    # Filtro y saco uniques
    df = df.loc[df.TIPO_PROCEDIMIENTO.isin(tipos_validos)]
    df = (df.groupby(['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).PROVEEDOR_CONTRATISTA.nunique()
          .reset_index()
          .rename(columns={'PROVEEDOR_CONTRATISTA': 'numero_proveedores'})
          .groupby(['CLAVEUC', 'numero_proveedores']).NUMERO_PROCEDIMIENTO.count()
          .reset_index()
          .rename(columns={'NUMERO_PROCEDIMIENTO': 'numero_procedimientos'})
          # Esta parte no me gusta pero de momento no se me ocurre otra forma
          .pivot(index='CLAVEUC', columns='numero_proveedores', values='numero_procedimientos')
          .fillna(0))
    df = (df * 100).divide(df.sum(axis=1), axis='index')
    df = df.rename(columns={1: col_name})
    if col_name not in df.columns:
        df = df.assign(col_name=0)
        # raise ValueError('Todos los procedimientos tuvieron mas de un participante')
    df = df.reset_index()
    # left join
    df_feature = pd.merge(df_feature, df.loc[:, ['CLAVEUC', col_name]],
                          on='CLAVEUC', how='left').fillna(0)
    return df_feature


def procedimientos_promedio_por_participantes(df, **kwargs):
    # tabla participantes
    if df.shape[0] == 0:
        return None
    df = df.copy()
    df_feature = (df.groupby(['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).PROVEEDOR_CONTRATISTA.nunique()
                    .reset_index()
                    .groupby('CLAVEUC', as_index=False).PROVEEDOR_CONTRATISTA.mean()
                    .assign(procs_promedio_por_participantes=lambda x: 1 / x.PROVEEDOR_CONTRATISTA)
                    .loc[:, ['CLAVEUC', 'procs_promedio_por_participantes']])
    return df_feature


def indice_participacion(df, **kwargs):
    # tabla participantes
    if df.shape[0] == 0:
        return None
    df = df.copy()
    df_participaciones = (df.groupby(['CLAVEUC', 'PROVEEDOR_CONTRATISTA'])
                            .NUMERO_PROCEDIMIENTO.nunique()
                            .reset_index()
                            .rename(columns={'NUMERO_PROCEDIMIENTO': 'participaciones'}))
    total_participaciones = (df_participaciones.groupby('CLAVEUC', as_index=False)
                                               .participaciones.sum()
                                               .rename(columns={'participaciones': 'tot_parts'}))
    df_feature = pd.merge(df_participaciones,
                          total_participaciones,
                          on='CLAVEUC', how='inner')
    df_feature = df_feature.assign(
        pc_partipaciones=df_feature.participaciones.divide(df_feature.tot_parts)
    )
    df_feature = (df_feature.groupby('CLAVEUC', as_index=False)
                            .pc_partipaciones.max()
                            .rename(columns={'pc_partipaciones': 'pc_partipaciones_promedio'}))
    df_feature = df_feature.loc[:, ['CLAVEUC', 'pc_partipaciones_promedio']]
    return df_feature


def procedimientos_por_participantes_unicos(df, **kwargs):
    # tabla participantes
    if df.shape[0] == 0:
        return None
    df = df.copy()
    df_procs = df.groupby('CLAVEUC').NUMERO_PROCEDIMIENTO.nunique().reset_index()
    df_parts = df.groupby('CLAVEUC').PROVEEDOR_CONTRATISTA.nunique().reset_index()
    df_feature = pd.merge(df_procs, df_parts, on='CLAVEUC', how='inner')
    df_feature = df_feature.assign(
        procs_por_participantes=df_feature.NUMERO_PROCEDIMIENTO / df_feature.PROVEEDOR_CONTRATISTA
    )
    df_feature = df_feature.loc[:, ['CLAVEUC', 'procs_por_participantes']]
    return df_feature


def tendencia_incremento_participantes(df, **kwargs):
    # participantes
    def _estimar_pendiente(row):
        # TODO: falta filtrar por nans
        y = row.values.reshape(-1, 1)
        x = np.arange(0, y.shape[0]).reshape(-1, 1)
        # model = Ridge(fit_intercept=False)
        model = Ridge(fit_intercept=True)
        model.fit(x, y)
        pendiente = model.coef_.flatten()[0]
        pendiente *= -1
        return pendiente
    if df.shape[0] == 0:
        return None
    df = df.copy()
    df = df.assign(
        Year=df.NUMERO_PROCEDIMIENTO.map(lambda x: int(x.split('-')[3]))
    )
    df = (df.groupby(['CLAVEUC', 'Year', 'NUMERO_PROCEDIMIENTO'])
            .PROVEEDOR_CONTRATISTA.nunique()
            .reset_index())
    df = df.groupby(
        ['CLAVEUC', 'Year'], as_index=False
    ).PROVEEDOR_CONTRATISTA.mean()
    df = (df.pivot(index='CLAVEUC',
                   columns='Year',
                   values='PROVEEDOR_CONTRATISTA')
            .loc[:, list(range(2012, 2018))]
            .fillna(0))
    df = df.assign(
        disminucion_participacion=df.apply(
            _estimar_pendiente, axis=1)
    ).reset_index()
    df = df.loc[:, ['CLAVEUC', 'disminucion_participacion']]
    return df

# def _crear_conexiones(df):
#     def _asignar_total_procs(row):
#         return procs_por_proveedor[row.poc_1] + procs_por_proveedor[row.poc_2]
#     procs_por_proveedor = (df.groupby('PROVEEDOR_CONTRATISTA')
#                              .NUMERO_PROCEDIMIENTO.count()
#                              .to_dict())
#     total_procs = df.NUMERO_PROCEDIMIENTO.nunique()
#     total_pocs = df.PROVEEDOR_CONTRATISTA.nunique()
#     # Se crea el grafo
#     bi_graph = nx.Graph()
#     bi_graph.add_nodes_from(df['PROVEEDOR_CONTRATISTA'], bipartite=0)
#     bi_graph.add_nodes_from(df['NUMERO_PROCEDIMIENTO'], bipartite=1)
#     edges = [
#         (row.PROVEEDOR_CONTRATISTA, row.NUMERO_PROCEDIMIENTO, 1)
#         for row in df.itertuples()
#     ]
#     bi_graph.add_weighted_edges_from(edges, weight='weight')
#     graph = bipartite.weighted_projected_graph(
#         bi_graph, df['PROVEEDOR_CONTRATISTA'].unique())
#     edges = [
#         {'poc_1': edge[0], 'poc_2': edge[1], 'weight': edge[2]['weight']}
#         for edge in graph.edges(data=True)
#     ]
#     df_edges = pd.DataFrame(edges)
#     # Casos sin procs en común
#     if df_edges.shape[0] == 0:
#         return None
#     # Removemos a los que tienen uno o menos
#     df_edges = df_edges.loc[df_edges.weight > 2]
#     if df_edges.shape[0] == 0:
#         return None
#     # sumo los contratos de los dos pocs
#     df_edges = df_edges.assign(suma_procs=df_edges.apply(_asignar_total_procs, axis=1))
#     # concentracion de participacion
#     score_participacion = df_edges.weight.divide(df_edges.suma_procs - df_edges.weight)
#     df_edges = df_edges.assign(total_procs=total_procs,
#                                total_pocs=total_pocs,
#                                score_participacion=score_participacion)
#     df_edges = df_edges.assign(
#         participacion_conjunta=(
#             df_edges.weight.divide(total_procs) * df_edges.score_participacion)
#     )
#     return df_edges
#
#
# def participacion_conjunta(df):
#     df = df.copy()
#     all_ucs = df.CLAVEUC.unique()
#     df_red = df.groupby(
#         ['CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'PROVEEDOR_CONTRATISTA'],
#         as_index=False).PRECIO_TOTAL.count()
#     df_red = df_red.drop('PRECIO_TOTAL', axis=1)
#     for uc in all_ucs:
#         pass


# def score_participacion
