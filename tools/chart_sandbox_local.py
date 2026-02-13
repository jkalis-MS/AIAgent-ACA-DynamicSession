"""Local (non-sandboxed) weather chart implementation."""
import os
import logging
import time
from typing import Annotated

logger = logging.getLogger(__name__)

# Import shared weather data fetcher
from .weather_sandbox_local import get_weather_data

# Chart output directory (next to the project root)
CHART_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'charts')


def _generate_chart(all_data: dict, chart_path: str) -> None:
    """
    Generate a multi-city weather comparison chart and save to disk.
    Separated so both local and ACA-fallback can reuse it.
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from datetime import datetime as dt

    colors = ['#2196F3', '#FF5722', '#4CAF50', '#9C27B0']

    fig, (ax_temp, ax_precip) = plt.subplots(
        2, 1, figsize=(14, 8), height_ratios=[3, 1],
        sharex=True, gridspec_kw={'hspace': 0.08}
    )
    fig.patch.set_facecolor('#1a1a2e')
    ax_temp.set_facecolor('#16213e')
    ax_precip.set_facecolor('#16213e')

    for idx, (city, data) in enumerate(all_data.items()):
        daily = data['daily']
        dates_list = [dt.strptime(d, '%Y-%m-%d') for d in daily['time']]
        highs = daily['temperature_2m_max']
        lows = daily['temperature_2m_min']
        precip = daily['precipitation_sum']
        color = colors[idx % len(colors)]

        ax_temp.plot(dates_list, highs, color=color, linewidth=2,
                     label=f"{city.title()} High", marker='o', markersize=3)
        ax_temp.plot(dates_list, lows, color=color, linewidth=1.5, linestyle='--',
                     label=f"{city.title()} Low", marker='o', markersize=2, alpha=0.7)
        ax_temp.fill_between(dates_list, lows, highs, color=color, alpha=0.08)

        bar_width = 0.6 / len(all_data)
        offset = (idx - len(all_data) / 2 + 0.5) * bar_width
        offset_dates = [mdates.date2num(d) + offset for d in dates_list]
        ax_precip.bar(offset_dates, precip, width=bar_width, color=color,
                      alpha=0.7, label=city.title())

    # Style temperature axis
    ax_temp.set_ylabel('Temperature (°F)', color='white', fontsize=11)
    ax_temp.tick_params(colors='white')
    ax_temp.legend(loc='upper right', fontsize=8, facecolor='#1a1a2e',
                   edgecolor='white', labelcolor='white')
    ax_temp.grid(axis='y', alpha=0.2, color='white')
    ax_temp.set_title('14-Day Weather Comparison', color='white',
                      fontsize=14, fontweight='bold', pad=12)
    for spine in ax_temp.spines.values():
        spine.set_color('#333')

    # Style precipitation axis
    ax_precip.set_ylabel('Precip (in)', color='white', fontsize=11)
    ax_precip.set_xlabel('Date', color='white', fontsize=11)
    ax_precip.tick_params(colors='white')
    ax_precip.legend(loc='upper right', fontsize=8, facecolor='#1a1a2e',
                     edgecolor='white', labelcolor='white')
    ax_precip.grid(axis='y', alpha=0.2, color='white')
    ax_precip.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax_precip.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.setp(ax_precip.xaxis.get_majorticklabels(), rotation=45, ha='right',
             color='white')
    for spine in ax_precip.spines.values():
        spine.set_color('#333')

    plt.tight_layout()
    fig.savefig(chart_path, format='png', dpi=120, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)


def _build_text_summary(all_data: dict) -> str:
    """Build a text summary table for the chart data."""
    lines = []
    for city, data in all_data.items():
        daily = data['daily']
        avg_high = sum(daily['temperature_2m_max']) / len(daily['temperature_2m_max'])
        avg_low = sum(daily['temperature_2m_min']) / len(daily['temperature_2m_min'])
        total_precip = sum(daily['precipitation_sum'])
        rainy_days = sum(1 for p in daily['precipitation_sum'] if p > 0.1)
        lines.append(
            f"  • {city.title()}: Avg High {avg_high:.0f}°F / Low {avg_low:.0f}°F | "
            f"Precip: {total_precip:.1f}in ({rainy_days} rainy days)"
        )
    return "\n".join(lines)


def chart_weather_local(
    destinations: Annotated[str, "Comma-separated list of destinations to chart (e.g. 'Miami, New York, Seattle')"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Generate a multi-city weather comparison chart (Local execution)."""
    start_time = time.time()

    city_list = [c.strip() for c in destinations.split(',') if c.strip()]
    if not city_list:
        return "⚠️ Please provide at least one destination."
    if len(city_list) > 4:
        city_list = city_list[:4]

    logger.info(f"📊 Local chart generation for: {', '.join(city_list)}")
    print(f"📊 Local chart generation for: {', '.join(city_list)}")

    # Fetch weather data for each city
    all_data = {}
    for city in city_list:
        data = get_weather_data(city, dates)
        if data.get('error'):
            return f"⚠️ {data['error']}"
        all_data[city] = data

    data_time = int((time.time() - start_time) * 1000)

    try:
        # Ensure output directory exists
        os.makedirs(CHART_DIR, exist_ok=True)
        filename = f"weather_{'_'.join(c.lower().replace(' ', '') for c in city_list)}_{int(time.time())}.png"
        chart_path = os.path.join(CHART_DIR, filename)

        _generate_chart(all_data, chart_path)
    except ImportError:
        return "⚠️ matplotlib is not installed. Run: pip install matplotlib"
    except Exception as e:
        return f"⚠️ Chart generation failed: {str(e)}"

    chart_time = int((time.time() - start_time) * 1000)

    # Start chart file server (if not already running) and get URL
    from .chart_server import ensure_chart_server, get_chart_url
    ensure_chart_server()
    chart_url = get_chart_url(filename)
    
    # Build response with file path + text summary
    city_names = ', '.join(c.title() for c in city_list)
    result = f"📊 Weather Comparison: {city_names}\n\n"
    result += f"📈 Chart: {chart_url}\n\n"
    result += f"Summary (14-day forecast):\n"
    result += _build_text_summary(all_data)

    execution_time = int((time.time() - start_time) * 1000)
    result += f"\n\n⏱️ Debug Timing (Local Execution):\n"
    result += f"  [1] Chart generated: {chart_time}ms\n"
    result += f"  [2] Total execution time: {execution_time}ms\n"
    result += f"  Infrastructure time: {execution_time - chart_time}ms"

    logger.info(f"✅ Local chart generated for {city_names} → {chart_path} ({execution_time}ms)")
    print(f"✅ Local chart generated for {city_names} → {chart_path} ({execution_time}ms)")

    return f"🏠 [Local Execution]\n{result}"
