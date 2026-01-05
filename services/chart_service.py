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
    """Generate interactive vertical bar chart for flight occupancy - each column represents a flight"""
    if not PLOTLY_AVAILABLE or not occupancy_data:
        return None
    
    # Prepare data
    flight_labels = []
    occupancy_values = []
    colors = []
    
    for row in occupancy_data:
        source = row.get('source', 'Unknown')
        dest = row.get('dest', 'Unknown')
        departure_time = row.get('departure_time')
        
        # Format flight label - include route and date if available
        if departure_time:
            try:
                # Try to parse and format the date
                if isinstance(departure_time, str):
                    from datetime import datetime
                    # Handle different datetime formats
                    if '.' in departure_time:
                        dt = datetime.strptime(departure_time.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    else:
                        dt = datetime.strptime(departure_time, '%Y-%m-%d %H:%M:%S')
                    date_str = dt.strftime('%m/%d/%Y')
                else:
                    date_str = str(departure_time)[:10]
                # Format label with line breaks for better display
                # Plotly supports <br> for line breaks
                flight_label = f"{source}<br>→ {dest}<br>{date_str}"
            except Exception as e:
                # Fallback to simple label if date parsing fails
                flight_label = f"{source} → {dest}"
        else:
            flight_label = f"{source} → {dest}"
        
        flight_labels.append(flight_label)
        occupancy = float(row['occupancy_percentage']) if row.get('occupancy_percentage') is not None else 0
        occupancy_values.append(occupancy)
        
        # Color coding based on occupancy
        if occupancy >= 80:
            colors.append('#28a745')  # Green for high
        elif occupancy >= 50:
            colors.append('#ffc107')  # Orange for medium
        else:
            colors.append('#dc3545')  # Red for low
    
    # Create vertical bar chart (columns)
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=flight_labels,
        y=occupancy_values,
        orientation='v',
        marker=dict(
            color=colors,
            line=dict(color='white', width=2),
            opacity=0.85
        ),
        text=[f'{val:.1f}%' for val in occupancy_values],
        textposition='outside',
        hovertemplate='<b>Flight: %{x}</b><br>Seats Bought: %{y:.1f}%<extra></extra>',
        name='Occupancy'
    ))
    
    fig.update_layout(
        title={
            'text': 'Average Flight Occupancy - Percentage of Seats Bought',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat, sans-serif'}
        },
        yaxis=dict(
            range=[0, max(occupancy_values) * 1.2 if occupancy_values else 100],
            title='Percentage of Seats Bought (%)'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Open Sans, sans-serif', size=11),
        margin=dict(l=80, r=80, t=80, b=180),
        height=550,
        showlegend=False,
        hovermode='closest',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#2c3e50',
            font_size=12,
            font_family='Open Sans, sans-serif'
        )
    )
    
    # Update axes with correct title font syntax
    fig.update_xaxes(
        title_text='Flight (Route)', 
        title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50'),
        tickangle=-45,
        tickfont=dict(size=10, family='Open Sans, sans-serif'),
        automargin=True
    )
    fig.update_yaxes(
        title_text='Percentage of Seats Bought (%)', 
        title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50')
    )
    
    return json.dumps(fig.to_dict(), indent=2)

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
        title={
            'text': 'Revenue by Aircraft Type',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat, sans-serif'}
        },
        barmode='group',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Open Sans, sans-serif', size=11),
        margin=dict(l=80, r=80, t=80, b=100),
        height=550,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
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
    
    return json.dumps(fig.to_dict(), indent=2)

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
        title={
            'text': 'Revenue by Aircraft Type',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat, sans-serif'}
        },
        barmode='group',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Open Sans, sans-serif', size=11),
        margin=dict(l=80, r=80, t=80, b=100),
        height=550,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
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
    
    return json.dumps(fig.to_dict(), indent=2)

def generate_employee_hours_chart(employee_data):
    """Generate interactive stacked bar chart for employee flight hours"""
    if not PLOTLY_AVAILABLE or not employee_data:
        return None
    
    names = []
    long_hours = []
    short_hours = []
    
    for row in employee_data:
        names.append(f"{row['first_name']} {row['last_name']}")
        long_hours.append(float(row['long_hours']) if row.get('long_hours') is not None else 0)
        short_hours.append(float(row['short_hours']) if row.get('short_hours') is not None else 0)
    
    fig = go.Figure()
    
    # Short flights (bottom)
    fig.add_trace(go.Bar(
        name='Short Flights (≤6h)',
        x=names,
        y=short_hours,
        marker=dict(color='#3498db', line=dict(color='white', width=1.5)),
        hovertemplate='<b>%{x}</b><br>Short Flights: %{y:.1f}h<extra></extra>'
    ))
    
    # Long flights (stacked on top)
    fig.add_trace(go.Bar(
        name='Long Flights (>6h)',
        x=names,
        y=long_hours,
        marker=dict(color='#e67e22', line=dict(color='white', width=1.5)),
        hovertemplate='<b>%{x}</b><br>Long Flights: %{y:.1f}h<extra></extra>'
    ))
    
    # Add total labels on top
    totals = [s + l for s, l in zip(short_hours, long_hours)]
    fig.add_trace(go.Scatter(
        x=names,
        y=totals,
        mode='text',
        text=[f'{t:.1f}h' if t > 0 else '' for t in totals],
        textposition='top center',
        textfont=dict(size=10, color='#2c3e50', family='Open Sans, sans-serif'),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title={
            'text': 'Employee Flight Hours (Long vs Short)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat, sans-serif'}
        },
        xaxis=dict(
            tickangle=-45
        ),
        barmode='stack',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Open Sans, sans-serif', size=11),
        margin=dict(l=80, r=80, t=80, b=140),
        height=550,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
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
    fig.update_xaxes(title_text='Employee', 
                     title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50'))
    fig.update_yaxes(title_text='Flight Hours', 
                     title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50'))
    
    return json.dumps(fig.to_dict(), indent=2)

def generate_cancellation_chart(cancellation_data):
    """Generate interactive stacked bar chart with cancellation rate line - שיעור ביטולי רכישות לפי חודש"""
    if not PLOTLY_AVAILABLE or not cancellation_data:
        return None
    
    from datetime import datetime
    
    months = []
    month_labels = []
    total_orders = []
    cancelled_orders = []
    active_orders = []
    cancellation_rates = []
    
    for row in sorted(cancellation_data, key=lambda x: x['month']):
        month_str = row['month']  # Format: 'YYYY-MM'
        total = int(row['total_orders']) if row.get('total_orders') is not None else 0
        cancelled = int(row['cancelled_orders']) if row.get('cancelled_orders') is not None else 0
        active = total - cancelled
        rate = float(row['cancellation_rate']) if row.get('cancellation_rate') is not None else 0
        
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
        title={
            'text': 'שיעור ביטולי רכישות לפי חודש<br><span style="font-size:14px;color:#666;">Monthly Cancellation Rate Analysis</span>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat, sans-serif'}
        },
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Open Sans, sans-serif', size=11),
        margin=dict(l=80, r=80, t=100, b=80),
        height=550,
        barmode='stack',  # Changed to stack
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
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
    
    return json.dumps(fig.to_dict(), indent=2)

def generate_plane_activity_chart(plane_data):
    """Generate interactive grouped bar chart for plane activity"""
    if not PLOTLY_AVAILABLE or not plane_data:
        return None
    
    # Organize data by aircraft and month
    aircraft_ids = sorted(set(row['aircraft_id'] for row in plane_data))
    months = sorted(set(row['month'] for row in plane_data))
    
    # Create matrices for flights performed
    flights_matrix = {}
    for aircraft_id in aircraft_ids:
        flights_matrix[aircraft_id] = {}
        for month in months:
            matching = [r for r in plane_data if r['aircraft_id'] == aircraft_id and r['month'] == month]
            if matching:
                flights_matrix[aircraft_id][month] = int(matching[0]['flights_performed']) if matching[0].get('flights_performed') is not None else 0
            else:
                flights_matrix[aircraft_id][month] = 0
    
    fig = go.Figure()
    
    # Generate colors for each aircraft
    colors = px.colors.qualitative.Set3[:len(aircraft_ids)]
    
    for i, aircraft_id in enumerate(aircraft_ids):
        flights = [flights_matrix[aircraft_id].get(month, 0) for month in months]
        fig.add_trace(go.Bar(
            name=f'Aircraft {aircraft_id}',
            x=months,
            y=flights,
            marker=dict(
                color=colors[i % len(colors)],
                line=dict(color='white', width=1.5)
            ),
            text=[str(val) if val > 0 else '' for val in flights],
            textposition='outside',
            hovertemplate=f'<b>Aircraft {aircraft_id}</b><br>Month: %{{x}}<br>Flights: %{{y}}<extra></extra>'
        ))
    
    fig.update_layout(
        title={
            'text': 'Plane Activity by Month',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Montserrat, sans-serif'}
        },
        barmode='group',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Open Sans, sans-serif', size=11),
        margin=dict(l=80, r=120, t=80, b=100),
        height=550,
        legend=dict(
            title='Aircraft ID',
            title_font=dict(size=12, family='Open Sans, sans-serif'),
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=1.02,
            font=dict(size=11, family='Open Sans, sans-serif')
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
    fig.update_xaxes(title_text='Month', 
                     title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50'))
    fig.update_yaxes(title_text='Flights Performed', 
                     title_font=dict(size=13, family='Open Sans, sans-serif', color='#2c3e50'))
    
    return json.dumps(fig.to_dict(), indent=2)
