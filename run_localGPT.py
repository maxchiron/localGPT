import click
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.llms import HuggingFacePipeline
from constants import CHROMA_SETTINGS, PERSIST_DIRECTORY
from transformers import LlamaTokenizer, LlamaForCausalLM, pipeline
import click
import os
# from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from transformers import LlamaForCausalLM, LlamaTokenizer, pipeline

from constants import CHROMA_SETTINGS, PERSIST_DIRECTORY

#os.environ['CUDA_VISIBLE_DEVICES']='1,2,3'


def load_model():
    """
    Select a model on huggingface.
    If you are running this for the first time, it will download a model for you.
    subsequent runs will use the model from the disk.
    """

    model_dict = {
    '1': 'TheBloke/vicuna-7B-1.1-HF',
    '2': 'TheBloke/Wizard-Vicuna-13B-Uncensored-HF',
    '3': 'NousResearch/Nous-Hermes-13b',
    '4': 'TheBloke/guanaco-65B-HF',
    }

    while True:
        user_input = input("""

                Type number than hit ENTER to Choose a Model:

                ---

                1 TheBloke/vicuna-7B-1.1-HF [Fastest]
                2 TheBloke/Wizard-Vicuna-13B-Uncensored-HF
                3 NousResearch/Nous-Hermes-13b [Recommand]
                4 TheBloke/guanaco-65B-HF [Biggest]
                (...or input other pytorch model full-name in format like: TheBloke/vicuna-7B-1.1-HF ...)
                
                ---
                I choose:
                """)
        if '/' in user_input:
            break
        elif int(user_input) > len(model_dict):
            print('Please type a correct number to choose a model.')
            continue
        else:
            break

    #model_id = "TheBloke/vicuna-7B-1.1-HF"

    if '/' in user_input:
        model_id = user_input
    else:
        model_id = model_dict[user_input]

    tokenizer = LlamaTokenizer.from_pretrained(model_id)

    model = LlamaForCausalLM.from_pretrained(
        model_id,
        #   load_in_8bit=True, # set these options if your GPU supports them!
        #   device_map=1#'auto',
        #   torch_dtype=torch.float16,
        #   low_cpu_mem_usage=True
    )

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=2048,
        temperature=0,
        top_p=0.95,
        repetition_penalty=1.15,
    )

    local_llm = HuggingFacePipeline(pipeline=pipe)

    return local_llm


@click.command()
@click.option(
    "--device_type",
    default="cuda",
    type=click.Choice(
        [
            "cpu",
            "cuda",
            "ipu",
            "xpu",
            "mkldnn",
            "opengl",
            "opencl",
            "ideep",
            "hip",
            "ve",
            "fpga",
            "ort",
            "xla",
            "lazy",
            "vulkan",
            "mps",
            "meta",
            "hpu",
            "mtia",
        ]
    ),
    help="Device to run on. (Default is cuda)",
)
def main(device_type):
    print(f"Running on: {device_type}")

    embeddings = HuggingFaceInstructEmbeddings(
        model_name="hkunlp/instructor-xl", model_kwargs={"device": device_type}
    )
    # load the vectorstore
    db = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings,
        client_settings=CHROMA_SETTINGS,
    )
    retriever = db.as_retriever()
    # Prepare the LLM
    # callbacks = [StreamingStdOutCallbackHandler()]
    # load the LLM for generating Natural Language responses.
    llm = load_model()
    qa = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True
    )
    # Interactive questions and answers
    while True:
        query = input("\nEnter a query: ")
        if query == "exit":
            break

        # Get the answer from the chain
        res = qa(query)
        answer, docs = res["result"], res["source_documents"]

        # Print the result
        print("\n\n> Question:")
        print(query)
        print("\n> Answer:")
        print(answer)

        # # Print the relevant sources used for the answer
        print(
            "----------------------------------SOURCE DOCUMENTS---------------------------"
        )
        for document in docs:
            print("\n> " + document.metadata["source"] + ":")
            print(document.page_content)
        print(
            "----------------------------------SOURCE DOCUMENTS---------------------------"
        )


if __name__ == "__main__":
    main()
