import json
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None
    make_subplots = None

def generate_occupancy_chart(occupancy_data):
    """Generate interactive gauge/indicator chart for average flight occupancy"""
    if not PLOTLY_AVAILABLE or not occupancy_data:
        return None
    
    try:
        # Extract the average occupancy rate (new query returns single row with avg_occupancy_rate)
        avg_occupancy = 0
        if occupancy_data and len(occupancy_data) > 0:
            # Convert from decimal (0.0-1.0) to percentage (0-100)
            occupancy_value = occupancy_data[0].get('avg_occupancy_rate', 0) if isinstance(occupancy_data[0], dict) else (occupancy_data[0] if occupancy_data[0] is not None else 0)
            if occupancy_value is None:
                occupancy_value = 0
            avg_occupancy = float(occupancy_value) * 100
        
        # Color coding based on occupancy level
        if avg_occupancy >= 80:
            color = '#28a745'  # Green for high
            status = 'Excellent'
        elif avg_occupancy >= 60:
            color = '#ffc107'  # Yellow for good
            status = 'Good'
        elif avg_occupancy >= 40:
            color = '#fd7e14'  # Orange for medium
            status = 'Moderate'
        else:
            color = '#dc3545'  # Red for low
            status = 'Low'
        
        # Create a gauge/indicator chart
        fig = go.Figure()
        
        # Add the gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=avg_occupancy,
            domain={'x': [0, 1], 'y': [0, 1]},
            number={
                'suffix': '%',
                'font': {'size': 50, 'family': 'Montserrat, sans-serif', 'color': color}
            },
            delta={
                'reference': 75,  # Target occupancy
                'increasing': {'color': '#28a745'},
                'decreasing': {'color': '#dc3545'},
                'position': 'bottom'
            },
            gauge={
                'axis': {
                    'range': [None, 100],
                    'tickwidth': 2,
                    'tickcolor': '#2c3e50',
                    'tickfont': {'size': 14, 'family': 'Open Sans, sans-serif'}
                },
                'bar': {'color': color, 'thickness': 0.75},
                'bgcolor': 'white',
                'borderwidth': 2,
                'bordercolor': '#e0e0e0',
                'steps': [
                    {'range': [0, 40], 'color': 'rgba(220, 53, 69, 0.15)'},
                    {'range': [40, 60], 'color': 'rgba(253, 126, 20, 0.15)'},
                    {'range': [60, 80], 'color': 'rgba(255, 193, 7, 0.15)'},
                    {'range': [80, 100], 'color': 'rgba(40, 167, 69, 0.15)'}
                ],
                'threshold': {
                    'line': {'color': '#6c757d', 'width': 3},
                    'thickness': 0.75,
                    'value': 75
                }
            }
        ))
        
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Open Sans, sans-serif', size=12),
            margin=dict(l=40, r=40, t=20, b=60),
            height=400,
            showlegend=False,
            annotations=[
                dict(
                    text='<b>Target: 75%</b>',
                    x=0.5,
                    y=-0.15,
                    xref='paper',
                    yref='paper',
                    showarrow=False,
                    font=dict(size=16, color='#2c3e50', family='Montserrat, sans-serif', weight='bold')
                )
            ]
        )
        
        return json.dumps(fig.to_dict())
    except Exception as e:
        print(f"Error generating occupancy chart: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_revenue_chart(revenue_data):
    """Generate interactive revenue chart with filters"""
    if not PLOTLY_AVAILABLE or not revenue_data:
        return None
    
    # Organize data by manufacturer and size
    data_dict = {}
    for row in revenue_data:
        key = f"{row['manufacturer']}_{'Large' if row['is_large'] else 'Small'}"
        if key not in data_dict:
            data_dict[key] = {'economy': 0, 'business': 0, 'manufacturer': row['manufacturer'], 'is_large': row['is_large']}
        
        revenue = float(row['total_revenue']) if row.get('total_revenue') is not None else 0
        if row['is_business']:
            data_dict[key]['business'] += revenue
        else:
            data_dict[key]['economy'] += revenue
    
    # Prepare grouped data
    x_labels = []
    economy_values = []
    business_values = []
    
    for key, values in sorted(data_dict.items()):
        size_label = 'Large' if values['is_large'] else 'Small'
        x_labels.append(f"{values['manufacturer']} ({size_label})")
        economy_values.append(values['economy'])
        business_values.append(values['business'])
    
    fig = go.Figure()
    
    # Economy bars
    fig.add_trace(go.Bar(
        name='Economy',
        x=x_labels,
        y=economy_values,
        # Remove explicit width - let Plotly handle it
        marker=dict(color='#3498db', line=dict(color='white', width=1.5)),
        text=[f'${val:,.0f}' if val > 0 else '' for val in economy_values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Economy: $%{y:,}<extra></extra>'
    ))
    
    # Business bars
    fig.add_trace(go.Bar(
        name='Business',
        x=x_labels,
        y=business_values,
        # Remove explicit width - let Plotly handle it
        marker=dict(color='#9b59b6', line=dict(color='white', width=1.5)),
        text=[f'${val:,.0f}' if val > 0 else '' for val in business_values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Business: $%{y:,}<extra></extra>'
    ))
    
    fig.update_layout(
        title=None,
        barmode='group',
        bargap=0.15,  # Consistent gap
        bargroupgap=0.1,  # Gap between groups
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Open Sans, sans-serif', size=11),
        margin=dict(l=80, r=80, t=30, b=100),
        height=550,
        legend=dict(
            orientation='h',
            yanchor='top',
            y=0.98,
            xanchor='right',
            x=1
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#2c3e50',
            font_size=12,
            font_family='Open Sans, sans-serif'
        )
    )
    
    # Update axes with correct title font syntax
    fig.update_xaxes(
        title_text='Aircraft Type', 
        title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50')
    )
    fig.update_yaxes(
        title_text='Revenue ($)', 
        title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50')
    )
    
    return json.dumps(fig.to_dict())

def generate_filtered_revenue_chart(revenue_data, manufacturer_filter=None, size_filter=None, class_filter=None):
    """Generate filtered revenue chart"""
    if not PLOTLY_AVAILABLE or not revenue_data:
        return None
    
    # Filter data based on parameters
    filtered_data = revenue_data.copy()
    
    if manufacturer_filter and manufacturer_filter != 'all':
        filtered_data = [row for row in filtered_data if row.get('manufacturer') == manufacturer_filter]
    
    if size_filter and size_filter != 'all':
        is_large = size_filter == 'large'
        filtered_data = [row for row in filtered_data if row.get('is_large') == is_large]
    
    if class_filter and class_filter != 'all':
        is_business = class_filter == 'business'
        filtered_data = [row for row in filtered_data if row.get('is_business') == is_business]
    
    if not filtered_data:
        return None
    
    # Organize filtered data
    data_dict = {}
    for row in filtered_data:
        key = f"{row['manufacturer']}_{'Large' if row['is_large'] else 'Small'}"
        if key not in data_dict:
            data_dict[key] = {'economy': 0, 'business': 0, 'manufacturer': row['manufacturer'], 'is_large': row['is_large']}
        
        revenue = float(row['total_revenue']) if row.get('total_revenue') is not None else 0
        if row['is_business']:
            data_dict[key]['business'] += revenue
        else:
            data_dict[key]['economy'] += revenue
    
    # Prepare grouped data
    x_labels = []
    economy_values = []
    business_values = []
    
    for key, values in sorted(data_dict.items()):
        size_label = 'Large' if values['is_large'] else 'Small'
        x_labels.append(f"{values['manufacturer']} ({size_label})")
        economy_values.append(values['economy'])
        business_values.append(values['business'])
    
    fig = go.Figure()
    
    # Economy bars
    fig.add_trace(go.Bar(
        name='Economy',
        x=x_labels,
        y=economy_values,
        marker=dict(color='#3498db', line=dict(color='white', width=1.5)),
        text=[f'${val:,.0f}' if val > 0 else '' for val in economy_values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Economy: $%{y:,}<extra></extra>'
    ))
    
    # Business bars
    fig.add_trace(go.Bar(
        name='Business',
        x=x_labels,
        y=business_values,
        marker=dict(color='#9b59b6', line=dict(color='white', width=1.5)),
        text=[f'${val:,.0f}' if val > 0 else '' for val in business_values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Business: $%{y:,}<extra></extra>'
    ))
    
    fig.update_layout(
        title=None,
        barmode='group',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Open Sans, sans-serif', size=11),
        margin=dict(l=80, r=80, t=30, b=100),
        height=550,
        legend=dict(
            orientation='h',
            yanchor='top',
            y=0.98,
            xanchor='right',
            x=1
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#2c3e50',
            font_size=12,
            font_family='Open Sans, sans-serif'
        )
    )
    
    # Update axes with correct title font syntax
    fig.update_xaxes(
        title_text='Aircraft Type', 
        title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50')
    )
    fig.update_yaxes(
        title_text='Revenue ($)', 
        title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50')
    )
    
    return json.dumps(fig.to_dict())

def generate_employee_hours_chart(employee_data):
    """Generate horizontal stacked bar chart for employee flight hours."""
    if not PLOTLY_AVAILABLE or not employee_data:
        return None

    try:
        # Filter out rows with no hours and handle None values
        valid_data = []
        for row in employee_data:
            total_hours = float(row.get('total_hours', 0) or 0)
            if total_hours > 0:  # Only include employees with flight hours
                valid_data.append(row)
        
        if not valid_data:
            return None
        
        sorted_data = sorted(
            valid_data,
            key=lambda x: float(x.get('total_hours', 0) or 0),
            reverse=True
        )

        # Use role in label (no id suffix), handle None values
        names = []
        long_hours = []
        short_hours = []
        
        for row in sorted_data:
            first_name = row.get('first_name') or 'Unknown'
            last_name = row.get('last_name') or 'Employee'
            role = row.get('role') or 'Employee'
            names.append(f"{first_name} {last_name} ({role})")
            
            long_val = row.get('long_hours')
            short_val = row.get('short_hours')
            long_hours.append(float(long_val) if long_val is not None else 0)
            short_hours.append(float(short_val) if short_val is not None else 0)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Short Flights (≤6h)',
            y=names,
            x=short_hours,
            orientation='h',
            marker=dict(color='#3498db', line=dict(width=0)),
            texttemplate='%{x:.1f}h',
            textposition='inside',
            textfont=dict(size=11, color='white'),
            textangle=0,
            insidetextanchor='middle',
            constraintext='inside',
            hovertemplate='<b>%{y}</b><br>Short Flights: %{x:.1f}h<extra></extra>'
        ))

        fig.add_trace(go.Bar(
            name='Long Flights (>6h)',
            y=names,
            x=long_hours,
            orientation='h',
            marker=dict(color='#e67e22', line=dict(width=0)),
            texttemplate='%{x:.1f}h',
            textposition='inside',
            textfont=dict(size=11, color='white'),
            textangle=0,
            insidetextanchor='middle',
            constraintext='inside',
            hovertemplate='<b>%{y}</b><br>Long Flights: %{x:.1f}h<extra></extra>'
        ))

        # Match Chart 5 layout to avoid the top gap issue.
        chart_height = max(800, len(names) * 80)

        fig.update_layout(
            barmode='stack',
            bargap=0.15,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Open Sans, sans-serif', size=13),
            margin=dict(l=150, r=40, t=6, b=80),
            height=chart_height,
            xaxis=dict(
                title='Flight Hours',
                title_font=dict(size=16),
                tickfont=dict(size=13),
                gridcolor='#e0e0e0'
            ),
            yaxis=dict(
                title='Employee',
                title_font=dict(size=16),
                tickfont=dict(size=13),
                autorange='reversed'
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.0,  # tight to top of plot
                xanchor='right',
                x=1,
                font=dict(size=13)
            ),
            hovermode='y unified',
            uniformtext=dict(minsize=11, mode='hide'),
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='#2c3e50',
                font_size=13,
                font_family='Open Sans, sans-serif'
            )
        )

        return json.dumps(fig.to_dict())
    except Exception as e:
        print(f"Error generating employee hours chart: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_cancellation_chart(cancellation_data):
    """Generate interactive stacked bar chart with cancellation rate line - שיעור ביטולי רכישות לפי חודש"""
    if not PLOTLY_AVAILABLE or not cancellation_data:
        return None
    
    try:
        from datetime import datetime
        
        if not cancellation_data or len(cancellation_data) == 0:
            return None
        
        months = []
        month_labels = []
        total_orders = []
        cancelled_orders = []
        active_orders = []
        cancellation_rates = []
        
        for row in sorted(cancellation_data, key=lambda x: x.get('month', '')):
            month_str = row.get('month', '')  # Format: 'YYYY-MM'
            if not month_str:
                continue
                
            total = int(row.get('total_orders', 0) or 0)
            cancelled = int(row.get('cancelled_orders', 0) or 0)
            active = total - cancelled
            rate_val = row.get('cancellation_rate')
            rate = float(rate_val) if rate_val is not None else 0.0
            
            # Format month label to simple format (e.g., "Nov 2025")
            try:
                dt = datetime.strptime(month_str, '%Y-%m')
                month_label = dt.strftime('%b %Y')  # e.g., "Nov 2025"
            except:
                month_label = month_str
            
            months.append(month_str)
            month_labels.append(month_label)
            total_orders.append(total)
            cancelled_orders.append(cancelled)
            active_orders.append(active)
            cancellation_rates.append(rate)
        
        # Create subplots with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Stacked bar chart - Active orders (bottom)
        fig.add_trace(
            go.Bar(
                name='Active Orders',
                x=month_labels,
                y=active_orders,
                # Remove explicit width - let Plotly handle it
                marker=dict(color='#28a745', opacity=0.8, line=dict(color='white', width=1.5)),
                hovertemplate='<b>%{x}</b><br>Active Orders: %{y}<extra></extra>'
            ),
            secondary_y=False,
        )
        
        # Stacked bar chart - Cancelled orders (on top of active)
        fig.add_trace(
            go.Bar(
                name='Cancelled Orders',
                x=month_labels,
                y=cancelled_orders,
                # Remove explicit width - let Plotly handle it
                marker=dict(color='#e74c3c', opacity=0.8, line=dict(color='white', width=1.5)),
                hovertemplate='<b>%{x}</b><br>Cancelled Orders: %{y}<extra></extra>'
            ),
            secondary_y=False,
        )
        
        # Line chart for cancellation rate
        fig.add_trace(
            go.Scatter(
                name='Cancellation Rate',
                x=month_labels,
                y=cancellation_rates,
                mode='lines+markers+text',
                marker=dict(color='#ffc107', size=12, line=dict(color='white', width=2)),
                line=dict(color='#ffc107', width=3, dash='dash'),
                text=[f'{rate:.1f}%' for rate in cancellation_rates],
                textposition='top center',
                textfont=dict(size=11, color='#f39c12', family='Open Sans, sans-serif', weight='bold'),
                hovertemplate='<b>%{x}</b><br>Cancellation Rate: %{y:.1f}%<extra></extra>'
            ),
            secondary_y=True,
        )
        
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Open Sans, sans-serif', size=11),
            margin=dict(l=80, r=80, t=40, b=80),
            height=550,
            barmode='stack',  # Changed to stack
            bargap=0.15,  # Match other charts
            legend=dict(
                orientation='h',
                yanchor='top',
                y=0.98,
                xanchor='right',
                x=1
            ),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='#2c3e50',
                font_size=12,
                font_family='Open Sans, sans-serif'
            )
        )
        
        # Set axes titles with correct font syntax
        fig.update_xaxes(
            title_text='חודש / Month', 
            title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50'),
            tickangle=0
        )
        fig.update_yaxes(
            title_text="מספר הזמנות / Number of Orders", 
            secondary_y=False, 
            title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50')
        )
        fig.update_yaxes(
            title_text="שיעור ביטול (%) / Cancellation Rate (%)", 
            secondary_y=True,
            title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50')
        )
        
        return json.dumps(fig.to_dict())
    except Exception as e:
        print(f"Error generating cancellation chart: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_plane_activity_chart(plane_data):
    """Generate horizontal bar chart with vertical scrolling for plane activity"""
    if not PLOTLY_AVAILABLE or not plane_data:
        return None
    
    try:
        if not plane_data or len(plane_data) == 0:
            return None
        
        # Group data by aircraft and calculate totals
        aircraft_stats = {}
        for row in plane_data:
            aircraft_id = row.get('aircraft_id')
            if aircraft_id is None:
                continue
                
            if aircraft_id not in aircraft_stats:
                aircraft_stats[aircraft_id] = {'performed': 0, 'cancelled': 0}
            
            performed = int(row.get('flights_performed', 0) or 0)
            cancelled = int(row.get('flights_cancelled', 0) or 0)
            aircraft_stats[aircraft_id]['performed'] += performed
            aircraft_stats[aircraft_id]['cancelled'] += cancelled
        
        if not aircraft_stats:
            return None
        
        # Sort by total activity (performed + cancelled)
        sorted_aircraft = sorted(
            aircraft_stats.items(),
            key=lambda x: x[1]['performed'] + x[1]['cancelled'],
            reverse=True
        )
        
        # Prepare data for horizontal bars
        aircraft_names = [f'Aircraft {aid}' for aid, _ in sorted_aircraft]
        performed_counts = [stats['performed'] for _, stats in sorted_aircraft]
        cancelled_counts = [stats['cancelled'] for _, stats in sorted_aircraft]
        
        fig = go.Figure()
        
        # Green bars for flights performed
        fig.add_trace(go.Bar(
            name='Flights Performed',
            y=aircraft_names,
            x=performed_counts,
            orientation='h',
            # NO width parameter - let Plotly auto-size to match vertical charts
            marker=dict(
                color='#28a745',
                line=dict(width=0)
            ),
            text=performed_counts,
            textposition='auto',
            textfont=dict(size=13),
            hovertemplate='<b>%{y}</b><br>Performed: %{x}<extra></extra>'
        ))
        
        # Red bars for flights cancelled
        fig.add_trace(go.Bar(
            name='Flights Cancelled',
            y=aircraft_names,
            x=cancelled_counts,
            orientation='h',
            # NO width parameter - let Plotly auto-size to match vertical charts
            marker=dict(
                color='#dc3545',
                line=dict(width=0)
            ),
            text=cancelled_counts,
            textposition='auto',
            textfont=dict(size=13),
            hovertemplate='<b>%{y}</b><br>Cancelled: %{x}<extra></extra>'
        ))
        
        # Match Chart 3 style and thickness.
        chart_height = max(800, len(aircraft_names) * 80)
        
        fig.update_layout(
            barmode='stack',  # Match Chart 3 style
            bargap=0.15,  # Match Chart 3 spacing
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Open Sans, sans-serif', size=13),
            margin=dict(l=150, r=80, t=12, b=80),  # Reduce gap above bars
            height=chart_height,
            xaxis=dict(
                title='Number of Flights',
                title_font=dict(size=16),
                gridcolor='#e0e0e0',
                tickfont=dict(size=13)
            ),
            yaxis=dict(
                title='Aircraft',
                title_font=dict(size=16),
                tickfont=dict(size=13),
                autorange='reversed'  # Top to bottom
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.005,  # just above bars without large gap
                xanchor='right',
                x=1,
                font=dict(size=13)
            ),
            hovermode='y unified'
        )
        
        return json.dumps(fig.to_dict())
    except Exception as e:
        print(f"Error generating plane activity chart: {e}")
        import traceback
        traceback.print_exc()
        return None
