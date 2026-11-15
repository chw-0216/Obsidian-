import json
import re
from datetime import datetime
from collections import defaultdict
import os

# Load the chat history
with open(r'C:\Users\wardc\Desktop\导_聊天记录.json', 'r', encoding='utf-8') as f:
    messages = json.load(f)

# Filter messages from deerluna
deerluna_messages = [msg for msg in messages if msg.get('senderUsername') == 'deerluna']

print(f"Total messages in chat: {len(messages)}")
print(f"Messages from deerluna: {len(deerluna_messages)}")

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
            'day_of_week': dt.weekday(),  # 0=Monday, 6=Sunday
            'date': dt.date()
        })

# Sort by timestamp
deerluna_data.sort(key=lambda x: x['timestamp'])

print(f"\nDate range: {deerluna_data[0]['timestamp'].strftime('%Y-%m-%d %H:%M')} to {deerluna_data[-1]['timestamp'].strftime('%Y-%m-%d %H:%M')}")

# Define emotion keywords
positive_keywords = [
    '好', '可以', '没问题', '明白', '收到', '感谢', '谢谢', '不错', '棒', '优秀',
    '漂亮', '完美', '太好了', '厉害', '赞', '加油', '继续', '支持', '鼓励', '积极',
    '开心', '高兴', '满意', '成功', '顺利', '完成', '达到', '实现', '突破', '进步'
]

negative_keywords = [
    '不好', '不行', '这不行', '问题', '困难', '麻烦', '担心', '焦虑', '着急', '紧张',
    '失望', '失败', '错误', '不对', '改', '修正', '调整', '重新', '撤回', '小心',
    '注意', '警告', '批评', '指责', '不满', '生气', '愤怒', '抱怨', '责怪', '催促'
]

neutral_keywords = [
    '呢', '吗', '吧', '啊', '哦', '嗯', '的', '了', '着', '过',
    '把', '被', '让', '给', '向', '从', '到', '在', '和', '与',
    '但', '而', '或', '如果', '因为', '所以', '虽然', '但是', '不过', '然而'
]

# Emotion analysis function
def analyze_emotion(text):
    text_lower = text.lower()
    
    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)
    neutral_count = sum(1 for word in neutral_keywords if word in text_lower)
    
    # Calculate emotion scores
    total_words = len(text_lower.split()) if text_lower.split() else 1
    
    positive_score = positive_count / total_words
    negative_score = negative_count / total_words
    neutral_score = neutral_count / total_words
    
    # Determine dominant emotion
    if positive_count > negative_count and positive_count > neutral_count:
        return 'positive', positive_score
    elif negative_count > positive_count and negative_count > neutral_count:
        return 'negative', negative_score
    else:
        return 'neutral', neutral_score

# Analyze emotions for each message
emotions = []
emotion_counts = defaultdict(int)
hourly_emotions = defaultdict(lambda: defaultdict(int))
daily_emotions = defaultdict(lambda: defaultdict(int))
topics = defaultdict(list)

for msg in deerluna_data:
    emotion, score = analyze_emotion(msg['content'])
    emotions.append({
        'timestamp': msg['timestamp'],
        'content': msg['content'],
        'emotion': emotion,
        'score': score,
        'hour': msg['hour'],
        'day_of_week': msg['day_of_week'],
        'date': msg['date']
    })
    
    emotion_counts[emotion] += 1
    hourly_emotions[msg['hour']][emotion] += 1
    daily_emotions[msg['day_of_week']][emotion] += 1
    
    # Extract topics (simple keyword extraction)
    content = msg['content']
    if '工作' in content or '日志' in content:
        topics['工作相关'].append((msg['timestamp'], content, emotion))
    if '招募' in content or '参与者' in content:
        topics['招募相关'].append((msg['timestamp'], content, emotion))
    if '海报' in content or '设计' in content:
        topics['设计相关'].append((msg['timestamp'], content, emotion))
    if '云南' in content or '怀柔' in content or '地点' in content:
        topics['地点相关'].append((msg['timestamp'], content, emotion))
    if '时间' in content or '几点' in content or '哪天' in content:
        topics['时间相关'].append((msg['timestamp'], content, emotion))
    if '关总' in content or '王总' in content or '领导' in content:
        topics['领导相关'].append((msg['timestamp'], content, emotion))

# Print emotion distribution
print("\n" + "="*60)
print("EMOTION DISTRIBUTION")
print("="*60)
total = len(emotions)
for emotion, count in emotion_counts.items():
    percentage = (count / total) * 100
    print(f"{emotion.capitalize()}: {count} messages ({percentage:.1f}%)")

# Print hourly patterns
print("\n" + "="*60)
print("HOURLY EMOTION PATTERNS")
print("="*60)
for hour in sorted(hourly_emotions.keys()):
    if hourly_emotions[hour]:
        total_hour = sum(hourly_emotions[hour].values())
        print(f"\n{hour:02d}:00-{hour:02d}:59 ({total_hour} messages):")
        for emotion, count in sorted(hourly_emotions[hour].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_hour) * 100
            print(f"  {emotion.capitalize()}: {count} ({percentage:.1f}%)")

# Print daily patterns
print("\n" + "="*60)
print("DAILY EMOTION PATTERNS")
print("="*60)
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
for day in sorted(daily_emotions.keys()):
    if daily_emotions[day]:
        total_day = sum(daily_emotions[day].values())
        print(f"\n{day_names[day]} ({total_day} messages):")
        for emotion, count in sorted(daily_emotions[day].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_day) * 100
            print(f"  {emotion.capitalize()}: {count} ({percentage:.1f}%)")

# Print topic analysis
print("\n" + "="*60)
print("TOPIC-BASED EMOTION ANALYSIS")
print("="*60)
for topic, msgs in topics.items():
    if msgs:
        print(f"\n{topic} ({len(msgs)} messages):")
        # Count emotions for this topic
        topic_emotions = defaultdict(int)
        for ts, content, emotion in msgs:
            topic_emotions[emotion] += 1
        
        for emotion, count in sorted(topic_emotions.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(msgs)) * 100
            print(f"  {emotion.capitalize()}: {count} ({percentage:.1f}%)")
        
        # Show example messages
        print("  Examples:")
        for i, (ts, content, emotion) in enumerate(msgs[:3]):
            print(f"    [{ts.strftime('%Y-%m-%d %H:%M')}] ({emotion}) {content[:50]}...")

# Find turning points (significant emotional shifts)
print("\n" + "="*60)
print("TURNING POINTS (SIGNIFICANT EMOTIONAL SHIFTS)")
print("="*60)

turning_points = []
for i in range(1, len(emotions)):
    prev_emotion = emotions[i-1]['emotion']
    curr_emotion = emotions[i]['emotion']
    
    # Check for significant shifts
    if prev_emotion != curr_emotion:
        # Calculate time difference
        time_diff = (emotions[i]['timestamp'] - emotions[i-1]['timestamp']).total_seconds() / 3600
        
        # Only consider shifts within reasonable time (e.g., same day or next day)
        if time_diff < 24:
            turning_points.append({
                'index': i,
                'timestamp': emotions[i]['timestamp'],
                'prev_content': emotions[i-1]['content'][:50],
                'curr_content': emotions[i]['content'][:50],
                'prev_emotion': prev_emotion,
                'curr_emotion': curr_emotion,
                'time_diff_hours': time_diff
            })

# Show top turning points
print(f"\nFound {len(turning_points)} turning points")
print("\nTop 10 most recent turning points:")
for i, tp in enumerate(turning_points[-10:]):
    print(f"\n{i+1}. {tp['timestamp'].strftime('%Y-%m-%d %H:%M')}")
    print(f"   Previous ({tp['prev_emotion']}): {tp['prev_content']}")
    print(f"   Current ({tp['curr_emotion']}): {tp['curr_content']}")
    print(f"   Time difference: {tp['time_diff_hours']:.1f} hours")

# Find specific examples of strong emotions
print("\n" + "="*60)
print("EXAMPLES OF STRONG EMOTIONAL MESSAGES")
print("="*60)

# Strong positive messages
print("\nStrong Positive Messages:")
strong_positive = [e for e in emotions if e['emotion'] == 'positive' and e['score'] > 0.3]
for msg in strong_positive[:5]:
    print(f"  [{msg['timestamp'].strftime('%Y-%m-%d %H:%M')}] {msg['content'][:60]}...")

# Strong negative messages
print("\nStrong Negative Messages:")
strong_negative = [e for e in emotions if e['emotion'] == 'negative' and e['score'] > 0.3]
for msg in strong_negative[:5]:
    print(f"  [{msg['timestamp'].strftime('%Y-%m-%d %H:%M')}] {msg['content'][:60]}...")

# Messages with specific emotional keywords
print("\n" + "="*60)
print("SPECIFIC EMOTIONAL KEYWORD EXAMPLES")
print("="*60)

# Find messages with specific keywords
keyword_examples = {
    '着急/anxiety': ['着急', '赶紧', '快', '马上', '尽快'],
    'disappointment': ['失望', '不好', '不行', '这不行'],
    'encouragement': ['加油', '继续', '支持', '鼓励'],
    'frustration': ['改', '修正', '重新', '撤回', '调整']
}

for emotion_name, keywords in keyword_examples.items():
    print(f"\n{emotion_name.upper()}:")
    for msg in deerluna_data:
        content = msg['content']
        if any(keyword in content for keyword in keywords):
            print(f"  [{msg['timestamp'].strftime('%Y-%m-%d %H:%M')}] {content[:60]}...")
            break  # Just show one example per emotion type

# Time-based analysis
print("\n" + "="*60)
print("TIME-BASED ANALYSIS")
print("="*60)

# Group by time periods
morning_msgs = [e for e in emotions if 6 <= e['hour'] < 12]
afternoon_msgs = [e for e in emotions if 12 <= e['hour'] < 18]
evening_msgs = [e for e in emotions if 18 <= e['hour'] < 24]
night_msgs = [e for e in emotions if 0 <= e['hour'] < 6]

print(f"\nMorning (6:00-12:00): {len(morning_msgs)} messages")
print(f"Afternoon (12:00-18:00): {len(afternoon_msgs)} messages")
print(f"Evening (18:00-24:00): {len(evening_msgs)} messages")
print(f"Night (0:00-6:00): {len(night_msgs)} messages")

# Emotion by time period
for period_name, period_msgs in [("Morning", morning_msgs), ("Afternoon", afternoon_msgs), 
                                   ("Evening", evening_msgs), ("Night", night_msgs)]:
    if period_msgs:
        period_emotions = defaultdict(int)
        for msg in period_msgs:
            period_emotions[msg['emotion']] += 1
        
        print(f"\n{period_name} Emotion Distribution:")
        for emotion, count in sorted(period_emotions.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(period_msgs)) * 100
            print(f"  {emotion.capitalize()}: {count} ({percentage:.1f}%)")

# Save analysis results to file
analysis_results = {
    'total_messages': len(messages),
    'deerluna_messages': len(deerluna_messages),
    'date_range': {
        'start': deerluna_data[0]['timestamp'].strftime('%Y-%m-%d %H:%M'),
        'end': deerluna_data[-1]['timestamp'].strftime('%Y-%m-%d %H:%M')
    },
    'emotion_distribution': dict(emotion_counts),
    'hourly_patterns': {str(k): dict(v) for k, v in hourly_emotions.items()},
    'daily_patterns': {str(k): dict(v) for k, v in daily_emotions.items()},
    'topic_analysis': {topic: len(msgs) for topic, msgs in topics.items()},
    'turning_points_count': len(turning_points),
    'strong_positive_count': len(strong_positive),
    'strong_negative_count': len(strong_negative)
}

with open(r'C:\Users\wardc\Desktop\emotion_analysis_results.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_results, f, ensure_ascii=False, indent=2)

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print(f"\nResults saved to: C:\\Users\\wardc\\Desktop\\emotion_analysis_results.json")
print(f"Total messages analyzed: {len(emotions)}")
print(f"Emotion distribution: {dict(emotion_counts)}")
print(f"Turning points found: {len(turning_points)}")
print(f"Strong positive messages: {len(strong_positive)}")
print(f"Strong negative messages: {len(strong_negative)}")
