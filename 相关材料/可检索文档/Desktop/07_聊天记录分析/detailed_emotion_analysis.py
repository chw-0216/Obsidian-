import json
import re
from datetime import datetime
from collections import defaultdict

# Load the chat history
with open(r'C:\Users\wardc\Desktop\导_聊天记录.json', 'r', encoding='utf-8') as f:
    messages = json.load(f)

# Filter messages from deerluna
deerluna_messages = [msg for msg in messages if msg.get('senderUsername') == 'deerluna']

# Convert timestamps to datetime objects and extract content
deerluna_data = []
for msg in deerluna_messages:
    timestamp = msg.get('createTime')
    content = msg.get('content', '')
    if timestamp and content:
        dt = datetime.fromtimestamp(timestamp)
        deerluna_data.append({
            'timestamp': dt,
            'content': content,
            'hour': dt.hour,
            'day_of_week': dt.weekday(),
            'date': dt.date(),
            'raw_content': msg.get('rawContent', '')
        })

# Sort by timestamp
deerluna_data.sort(key=lambda x: x['timestamp'])

# Enhanced emotion analysis with more nuanced scoring
def analyze_emotion_detailed(text):
    text_lower = text.lower()
    
    # Expanded keyword lists with weights
    positive_keywords = {
        '好': 1.0, '可以': 0.8, '没问题': 1.0, '明白': 0.6, '收到': 0.5, 
        '感谢': 1.0, '谢谢': 1.0, '不错': 0.9, '棒': 1.0, '优秀': 1.0,
        '漂亮': 0.9, '完美': 1.0, '太好了': 1.0, '厉害': 1.0, '赞': 1.0,
        '加油': 0.8, '继续': 0.6, '支持': 0.7, '鼓励': 0.8, '积极': 0.7,
        '开心': 1.0, '高兴': 1.0, '满意': 0.9, '成功': 1.0, '顺利': 0.9,
        '完成': 0.7, '达到': 0.6, '实现': 0.6, '突破': 0.8, '进步': 0.7,
        '辛苦': 0.5, '辛苦了': 0.8, '不错': 0.8, '很好': 0.9, '非常好': 1.0,
        '太棒了': 1.0, '优秀': 0.9, '出色': 0.9, '精彩': 0.9, '完美': 1.0
    }
    
    negative_keywords = {
        '不好': 0.8, '不行': 0.9, '这不行': 1.0, '问题': 0.6, '困难': 0.7,
        '麻烦': 0.6, '担心': 0.7, '焦虑': 0.8, '着急': 0.7, '紧张': 0.7,
        '失望': 0.9, '失败': 0.9, '错误': 0.7, '不对': 0.7, '改': 0.5,
        '修正': 0.6, '调整': 0.5, '重新': 0.6, '撤回': 0.7, '小心': 0.6,
        '注意': 0.5, '警告': 0.7, '批评': 0.8, '指责': 0.8, '不满': 0.8,
        '生气': 0.9, '愤怒': 1.0, '抱怨': 0.8, '责怪': 0.8, '催促': 0.6,
        '尽快': 0.5, '赶紧': 0.6, '快点': 0.6, '马上': 0.5, '立刻': 0.6
    }
    
    # Calculate weighted scores
    positive_score = 0
    negative_score = 0
    
    for word, weight in positive_keywords.items():
        if word in text_lower:
            positive_score += weight
    
    for word, weight in negative_keywords.items():
        if word in text_lower:
            negative_score += weight
    
    # Normalize scores
    total_words = len(text_lower.split()) if text_lower.split() else 1
    
    # Determine emotion with more nuanced thresholds
    if positive_score > 0 and negative_score == 0:
        return 'positive', positive_score / total_words
    elif negative_score > 0 and positive_score == 0:
        return 'negative', negative_score / total_words
    elif positive_score > negative_score and positive_score > 0:
        return 'mixed_positive', (positive_score - negative_score) / total_words
    elif negative_score > positive_score and negative_score > 0:
        return 'mixed_negative', (negative_score - positive_score) / total_words
    else:
        return 'neutral', 0

# Analyze emotions with detailed scoring
detailed_emotions = []
for msg in deerluna_data:
    emotion, score = analyze_emotion_detailed(msg['content'])
    detailed_emotions.append({
        'timestamp': msg['timestamp'],
        'content': msg['content'],
        'emotion': emotion,
        'score': score,
        'hour': msg['hour'],
        'day_of_week': msg['day_of_week'],
        'date': msg['date']
    })

# Find messages with specific emotional patterns
print("="*80)
print("DETAILED EMOTIONAL ANALYSIS FOR DEERLUNA")
print("="*80)

# 1. Messages showing frustration or urgency
print("\n1. MESSAGES SHOWING FRUSTRATION OR URGENCY:")
print("-"*60)
frustration_keywords = ['这不行', '不好', '不行', '改', '修正', '重新', '调整', '撤回']
frustration_messages = []
for msg in detailed_emotions:
    if any(keyword in msg['content'] for keyword in frustration_keywords):
        frustration_messages.append(msg)

for msg in frustration_messages[:10]:
    print(f"[{msg['timestamp'].strftime('%Y-%m-%d %H:%M')}] ({msg['emotion']}) {msg['content'][:80]}...")

# 2. Messages showing concern or care
print("\n2. MESSAGES SHOWING CONCERN OR CARE:")
print("-"*60)
concern_keywords = ['小心', '注意', '担心', '安全', '路上小心', '早点', '休息']
concern_messages = []
for msg in detailed_emotions:
    if any(keyword in msg['content'] for keyword in concern_keywords):
        concern_messages.append(msg)

for msg in concern_messages[:10]:
    print(f"[{msg['timestamp'].strftime('%Y-%m-%d %H:%M')}] ({msg['emotion']}) {msg['content'][:80]}...")

# 3. Messages showing encouragement or positive feedback
print("\n3. MESSAGES SHOWING ENCOURAGEMENT OR POSITIVE FEEDBACK:")
print("-"*60)
encouragement_keywords = ['好', '可以', '不错', '继续', '加油', '支持', '鼓励', '棒']
encouragement_messages = []
for msg in detailed_emotions:
    if any(keyword in msg['content'] for keyword in encouragement_keywords):
        encouragement_messages.append(msg)

for msg in encouragement_messages[:10]:
    print(f"[{msg['timestamp'].strftime('%Y-%m-%d %H:%M')}] ({msg['emotion']}) {msg['content'][:80]}...")

# 4. Messages with specific time pressure
print("\n4. MESSAGES WITH TIME PRESSURE:")
print("-"*60)
time_pressure_keywords = ['尽快', '赶紧', '快', '马上', '立刻', '今天', '明天', '这周']
time_pressure_messages = []
for msg in detailed_emotions:
    if any(keyword in msg['content'] for keyword in time_pressure_keywords):
        time_pressure_messages.append(msg)

for msg in time_pressure_messages[:10]:
    print(f"[{msg['timestamp'].strftime('%Y-%m-%d %H:%M')}] ({msg['emotion']}) {msg['content'][:80]}...")

# 5. Emotional transitions in conversation
print("\n5. EMOTIONAL TRANSITIONS IN CONVERSATION:")
print("-"*60)
transitions = []
for i in range(1, len(detailed_emotions)):
    prev_emotion = detailed_emotions[i-1]['emotion']
    curr_emotion = detailed_emotions[i]['emotion']
    
    if prev_emotion != curr_emotion:
        # Check for significant emotional shifts
        if (prev_emotion == 'positive' and curr_emotion in ['negative', 'mixed_negative']) or \
           (prev_emotion == 'negative' and curr_emotion in ['positive', 'mixed_positive']):
            transitions.append({
                'timestamp': detailed_emotions[i]['timestamp'],
                'prev_content': detailed_emotions[i-1]['content'][:50],
                'curr_content': detailed_emotions[i]['content'][:50],
                'prev_emotion': prev_emotion,
                'curr_emotion': curr_emotion
            })

print(f"Found {len(transitions)} significant emotional transitions")
for i, trans in enumerate(transitions[:5]):
    print(f"\n{i+1}. [{trans['timestamp'].strftime('%Y-%m-%d %H:%M')}]")
    print(f"   Previous ({trans['prev_emotion']}): {trans['prev_content']}")
    print(f"   Current ({trans['curr_emotion']}): {trans['curr_content']}")

# 6. Topic-specific emotional analysis
print("\n6. TOPIC-SPECIFIC EMOTIONAL ANALYSIS:")
print("-"*60)

topic_analysis = {
    '工作日志': [],
    '招募参与者': [],
    '海报设计': [],
    '地点安排': [],
    '时间安排': [],
    '领导沟通': [],
    '技术问题': []
}

for msg in detailed_emotions:
    content = msg['content']
    if '工作日志' in content or '工作' in content and '日志' in content:
        topic_analysis['工作日志'].append(msg)
    if '招募' in content or '参与者' in content or '首单' in content:
        topic_analysis['招募参与者'].append(msg)
    if '海报' in content or '设计' in content or '制版' in content:
        topic_analysis['海报设计'].append(msg)
    if '云南' in content or '怀柔' in content or '地点' in content or '地址' in content:
        topic_analysis['地点安排'].append(msg)
    if '时间' in content or '几点' in content or '哪天' in content or '周末' in content:
        topic_analysis['时间安排'].append(msg)
    if '关总' in content or '王总' in content or '领导' in content or '总' in content:
        topic_analysis['领导沟通'].append(msg)
    if '问题' in content or '困难' in content or '技术' in content or '版' in content:
        topic_analysis['技术问题'].append(msg)

for topic, messages in topic_analysis.items():
    if messages:
        emotion_counts = defaultdict(int)
        for msg in messages:
            emotion_counts[msg['emotion']] += 1
        
        print(f"\n{topic} ({len(messages)} messages):")
        for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(messages)) * 100
            print(f"  {emotion}: {count} ({percentage:.1f}%)")
        
        # Show most emotional message in this topic
        most_emotional = max(messages, key=lambda x: abs(x['score']))
        print(f"  Most emotional: [{most_emotional['timestamp'].strftime('%Y-%m-%d %H:%M')}] {most_emotional['content'][:60]}...")

# 7. Time-based emotional patterns
print("\n7. TIME-BASED EMOTIONAL PATTERNS:")
print("-"*60)

# Analyze by day of week
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
daily_emotions = defaultdict(lambda: defaultdict(int))

for msg in detailed_emotions:
    daily_emotions[msg['day_of_week']][msg['emotion']] += 1

for day in sorted(daily_emotions.keys()):
    total = sum(daily_emotions[day].values())
    print(f"\n{day_names[day]} ({total} messages):")
    for emotion, count in sorted(daily_emotions[day].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        print(f"  {emotion}: {count} ({percentage:.1f}%)")

# 8. Find specific examples of emotional escalation
print("\n8. EXAMPLES OF EMOTIONAL ESCALATION:")
print("-"*60)

# Find sequences where emotion intensifies
escalation_sequences = []
for i in range(2, len(detailed_emotions)):
    prev2_emotion = detailed_emotions[i-2]['emotion']
    prev1_emotion = detailed_emotions[i-1]['emotion']
    curr_emotion = detailed_emotions[i]['emotion']
    
    # Check for escalation pattern (e.g., neutral -> negative -> more negative)
    if prev2_emotion == 'neutral' and prev1_emotion in ['negative', 'mixed_negative'] and curr_emotion in ['negative', 'mixed_negative']:
        escalation_sequences.append({
            'start': detailed_emotions[i-2]['timestamp'],
            'middle': detailed_emotions[i-1]['timestamp'],
            'end': detailed_emotions[i]['timestamp'],
            'start_content': detailed_emotions[i-2]['content'][:40],
            'middle_content': detailed_emotions[i-1]['content'][:40],
            'end_content': detailed_emotions[i]['content'][:40]
        })

print(f"Found {len(escalation_sequences)} escalation sequences")
for i, seq in enumerate(escalation_sequences[:3]):
    print(f"\n{i+1}. Escalation sequence:")
    print(f"   [{seq['start'].strftime('%Y-%m-%d %H:%M')}] (neutral) {seq['start_content']}")
    print(f"   [{seq['middle'].strftime('%Y-%m-%d %H:%M')}] (negative) {seq['middle_content']}")
    print(f"   [{seq['end'].strftime('%Y-%m-%d %H:%M')}] (negative) {seq['end_content']}")

# 9. Find messages with emotional emojis or expressions
print("\n9. MESSAGES WITH EMOTIONAL EXPRESSIONS:")
print("-"*60)

emotional_expressions = [
    ('[捂脸]', 'facepalm/frustration'),
    ('[疑问]', 'confusion/questioning'),
    ('[嘘]', 'secret/whisper'),
    ('[勾引]', 'teasing/playful'),
    ('[破涕为笑]', 'tears turning to laughter')
]

for emoji, meaning in emotional_expressions:
    emoji_messages = [msg for msg in detailed_emotions if emoji in msg['content']]
    if emoji_messages:
        print(f"\n{emoji} ({meaning}) - {len(emoji_messages)} messages:")
        for msg in emoji_messages[:3]:
            print(f"  [{msg['timestamp'].strftime('%Y-%m-%d %H:%M')}] {msg['content'][:60]}...")

# 10. Summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

total_messages = len(detailed_emotions)
emotion_counts = defaultdict(int)
for msg in detailed_emotions:
    emotion_counts[msg['emotion']] += 1

print(f"\nTotal messages analyzed: {total_messages}")
print(f"\nEmotion distribution:")
for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / total_messages) * 100
    print(f"  {emotion}: {count} ({percentage:.1f}%)")

# Find most emotional days
print(f"\nMost emotional days:")
daily_emotion_intensity = defaultdict(float)
for msg in detailed_emotions:
    if msg['emotion'] in ['positive', 'negative', 'mixed_positive', 'mixed_negative']:
        daily_emotion_intensity[msg['date']] += abs(msg['score'])

top_emotional_days = sorted(daily_emotion_intensity.items(), key=lambda x: x[1], reverse=True)[:5]
for date, intensity in top_emotional_days:
    print(f"  {date}: intensity score {intensity:.2f}")

# Find peak emotional hours
print(f"\nPeak emotional hours:")
hourly_emotion_intensity = defaultdict(float)
for msg in detailed_emotions:
    if msg['emotion'] in ['positive', 'negative', 'mixed_positive', 'mixed_negative']:
        hourly_emotion_intensity[msg['hour']] += abs(msg['score'])

top_emotional_hours = sorted(hourly_emotion_intensity.items(), key=lambda x: x[1], reverse=True)[:5]
for hour, intensity in top_emotional_hours:
    print(f"  {hour:02d}:00-{hour:02d}:59: intensity score {intensity:.2f}")

# Save detailed results
detailed_results = {
    'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_messages': total_messages,
    'emotion_distribution': dict(emotion_counts),
    'frustration_messages_count': len(frustration_messages),
    'concern_messages_count': len(concern_messages),
    'encouragement_messages_count': len(encouragement_messages),
    'time_pressure_messages_count': len(time_pressure_messages),
    'emotional_transitions_count': len(transitions),
    'escalation_sequences_count': len(escalation_sequences),
    'topic_analysis': {topic: len(msgs) for topic, msgs in topic_analysis.items()},
    'top_emotional_days': [(str(date), intensity) for date, intensity in top_emotional_days],
    'top_emotional_hours': [(hour, intensity) for hour, intensity in top_emotional_hours]
}

with open(r'C:\Users\wardc\Desktop\detailed_emotion_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(detailed_results, f, ensure_ascii=False, indent=2)

print(f"\nDetailed analysis saved to: C:\\Users\\wardc\\Desktop\\detailed_emotion_analysis.json")
