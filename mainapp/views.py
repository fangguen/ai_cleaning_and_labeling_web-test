import json
import logging
import openai
import os
import tiktoken
import traceback
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
from openai import OpenAIError

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_API_BASE)

# 默认的清洗和标注维度
DEFAULT_CLEANING_DIMENSIONS = [
    "去除无关内容",
    "处理缺失和不完整数据",
    "数据规范化",
    "去除特殊字符和标点",
    "停用词处理",
    "分词和词形还原",
    "处理重复和冗余信息",
    "匿名化和隐私保护",
    "纠正语法和拼写错误"
]

DEFAULT_ANNOTATION_DIMENSIONS = [
    "情感和情绪标注",
    "心理症状标注",
    "意图和对话行为标注",
    "主题和内容标注",
    "实体识别和匿名化"
]


# 使用tiktoken计算token数量
def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


# 文本切片函数
def split_text(text, max_tokens=3072):
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = num_tokens_from_string(paragraph)
        
        if current_tokens + paragraph_tokens > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph
            current_tokens = paragraph_tokens
        else:
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            current_tokens += paragraph_tokens

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


# AI处理函数
def ai_process_chunk(chunk, process_type, dimensions):
    prompt = f"""请将以下对话内容进行处理并转为json格式的对话，每个对话轮次应包含"input"和"output"字段。
    "input"表示咨询者说的话，"output"表示咨询师的回复。请确保返回的是有效的JSON格式。

    对话内容：
    {chunk}

    请按照以下维度{process_type}对话内容：
    {', '.join(dimensions)}

    示例输出格式：
    {{
        "conversations": [
            {{
                "input": "最近我觉得自己压力很大，生活中的事情都让人喘不过气来，我经常感到很焦虑，不知道该怎么办。",
                "output": "听起来你正经历着很大的压力，这一定让你感到很不安。能和我分享一下，是什么事情让你感到焦虑呢？"
            }},
            {{
                "input": "咨询者的下一句话",
                "output": "咨询师的下一句回复"
            }}
        ]
    }}
    """
    
    try:
        logger.info("开始调用AI API")
        response = client.chat.completions.create(
            model='deepseek-chat',
            messages=[
                {"role": "system", "content": "你是一个帮助处理对话数据的助手。你的回答必须是有效的JSON格式。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4000,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        logger.info("AI API调用完成")

        result = response.choices[0].message.content.strip()
        logger.info(f"AI返回原始结果: {result}")

        try:
            parsed_result = json.loads(result)
            logger.info("AI返回结果成功解析为JSON")
            return parsed_result
        except json.JSONDecodeError as json_error:
            logger.error(f"AI返回的结果不是有效的JSON: {result}")
            logger.error(f"JSON解析错误: {str(json_error)}")
            return {"error": "AI返回的结果不是有效的JSON", "raw_result": result}

    except openai.APITimeoutError as e:
        logger.error(f"API 超时错误: {str(e)}")
        return {"error": f"API 超时错误: {str(e)}"}
    except openai.APIConnectionError as e:
        logger.error(f"API 连接错误: {str(e)}")
        return {"error": f"API 连接错误: {str(e)}"}
    except Exception as e:
        logger.error(f"AI处理出错: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": f"AI处理出错: {str(e)}"}


def index(request):
    context = {
        'cleaning_dimensions': json.dumps(DEFAULT_CLEANING_DIMENSIONS),
        'annotation_dimensions': json.dumps(DEFAULT_ANNOTATION_DIMENSIONS),
    }
    return render(request, 'index.html', context)


def handle_uploaded_file(f):
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f.name)

    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return file_path


def ai_data_cleaning(content, dimensions):
    prompt = f"请按照以下维度清洗文本数据：\n{', '.join(dimensions)}\n\n文本内容：\n{content}"

    try:
        response = client.chat.completions.create(
            model='deepseek-chat',
            messages=[
                {"role": "system", "content": "你是一个帮助清洗文本数据的助手"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
            temperature=0.5,
        )

        cleaned_data = response.choices[0].message.content.strip()
        return cleaned_data

    except Exception as e:
        raise Exception(f"AI数据清洗出错: {e}")


def ai_data_labeling(content, dimensions):
    prompt = f"请按照以下维度标注文本数据：\n{', '.join(dimensions)}\n\n文本内容：\n{content}"

    try:
        response = client.chat.completions.create(
            model='deepseek-chat',
            messages=[
                {"role": "system", "content": "你是一个帮助标注文本数据的助手"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
            temperature=0.5,
        )

        labeled_data = response.choices[0].message.content.strip()
        return labeled_data

    except Exception as e:
        raise Exception(f"AI数据标注出错: {e}")


@csrf_exempt
def process_file(request):
    if request.method == 'POST':
        try:
            logger.info("开始处理文件")
            data = json.loads(request.body)
            process_type = data.get('process_type')
            content = data.get('content')
            dimensions = data.get('dimensions', [])

            logger.info(f"处理类型: {process_type}")
            logger.info(f"维度: {dimensions}")
            logger.debug(f"内容: {content[:100]}...")  # 只记录前100个字符

            if not content:
                logger.warning("未提供内容")
                return JsonResponse({'error': '未提供内容'}, status=400)

            chunks = split_text(content, max_tokens=3072)
            logger.info(f"文本被分割成 {len(chunks)} 个块")

            results = []
            for i, chunk in enumerate(chunks):
                logger.info(f"开始处理第 {i+1} 个块")
                try:
                    result = ai_process_chunk(chunk, process_type, dimensions)
                    logger.info(f"第 {i+1} 个块处理完成")
                    logger.debug(f"第 {i+1} 个块结果: {result}")
                    if isinstance(result, dict) and 'conversations' in result:
                        results.extend(result['conversations'])
                    else:
                        results.append(result)
                except Exception as chunk_error:
                    logger.error(f"处理第 {i+1} 个块时出错: {str(chunk_error)}")
                    logger.error(traceback.format_exc())
                    results.append({"error": f"处理第 {i+1} 个块时出错: {str(chunk_error)}"})

            # 保存结果为JSON文件
            file_name = f"{process_type}_result.json"
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                logger.info(f"结果已保存到 {file_path}")
            except Exception as save_error:
                logger.error(f"保存结果时出错: {str(save_error)}")
                logger.error(traceback.format_exc())
                return JsonResponse({'error': f'保存结果时出错: {str(save_error)}'}, status=500)

            logger.info("文件处理完成，返回结果")
            return JsonResponse({'result': results, 'file_path': file_path})

        except json.JSONDecodeError as e:
            logger.error(f"JSON解码错误: {str(e)}")
            logger.error(f"接收到的数据: {request.body}")
            return JsonResponse({'error': '无效的JSON数据'}, status=400)
        except Exception as e:
            logger.error(f"处理文件时发生未知错误: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': f'处理文件时发生未知错误: {str(e)}'}, status=500)
    else:
        logger.warning(f"收到无效的请求方法: {request.method}")
        return JsonResponse({'error': '无效的请求方法'}, status=405)


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'error': '未上传文件'}, status=400)
        try:
            content = uploaded_file.read().decode('utf-8')
            return JsonResponse({'content': content})
        except UnicodeDecodeError:
            return JsonResponse({'error': '无法解码文件内容'}, status=400)
    return JsonResponse({'error': '无效的请求方法'}, status=405)


@csrf_exempt
def chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message', '')
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                stream=False
            )
            reply = response.choices[0].message.content
            return JsonResponse({'reply': reply})
        except Exception as e:
            logger.error(f"AI聊天出错: {e}")
            return JsonResponse({'error': '处理聊天消息时出错，请稍后重试。'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

