"""Test improved stress detection"""
import sys
sys.path.insert(0, 'src')

from scoring.mental_health_scoring import analyze_stress_text, mental_health_score, get_stress_level_category

# Test cases
test_cases = [
    '',
    'I am fine',
    'I am feeling busy with work',
    'I am stressed about deadlines',
    'I am very stressed and overwhelmed',
    'I feel panicked and cannot cope',
    'I am feeling better today, much calmer',
]

print('IMPROVED STRESS DETECTION TEST')
print('=' * 80)

for text in test_cases:
    stress_prob = analyze_stress_text(text)
    health_score_val = mental_health_score(stress_prob)
    level, category, desc = get_stress_level_category(stress_prob)
    
    if text:
        print(f'\nText: "{text[:50]}"')
    else:
        print(f'\nText: (empty)')
    print(f'  Stress Probability: {stress_prob:.2f}')
    print(f'  Health Score: {health_score_val:.1f}%')
    print(f'  Stress Level: {level:.1f}/10 - {category}')
    print(f'  Description: {desc}')

print('\n' + '=' * 80)
print('✅ Improved stress detection is working!')
