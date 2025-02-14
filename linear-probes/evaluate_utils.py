import torch as t

def evaluate_probe_on_string(prompt, model, tokenizer, probe, tqa_dataset, device, tokens_to_average=5):
    """
    Evaluate probe on a single string and return averaged probe output
    
    Args:
        prompt: String to evaluate
        model: Language model
        tokenizer: Tokenizer for the model
        probe: Linear probe model
        tqa_dataset: Dataset object containing activation cache
        device: Device to run model on
        tokens_to_average: Number of final tokens to average probe outputs over
        
    Returns:
        float: Average probe output for the string
    """
    tokens = tokenizer.encode(prompt, return_tensors="pt").to(device)
    
    with t.no_grad():
        tqa_dataset.activation_cache.clear_activations()
        model.forward(tokens)
        activations = tqa_dataset.activation_cache.activations[0][0]
        
        # Get last n token activations and average their probe outputs
        last_n_activations = activations[-tokens_to_average:]
        probe_outputs = [round(probe.evaluate_single_activation(t.tensor(act)), 4) for act in last_n_activations]
        avg_probe_output = sum(probe_outputs) / len(probe_outputs)
        
    return avg_probe_output, probe_outputs

def evaluate_probe_on_dataset(test_df, model, tokenizer, probe, tqa_dataset, device, tokens_to_average=5, verbose=True):
    """
    Evaluate probe on a test dataset and return probe outputs and accuracy
    
    Args:
        test_df: DataFrame containing prompts and labels
        model: Language model
        tokenizer: Tokenizer for the model
        probe: Linear probe model
        tqa_dataset: Dataset object containing activation cache
        device: Device to run model on
        tokens_to_average: Number of final tokens to average probe outputs over
        verbose: Whether to print progress
        
    Returns:
        tuple: (average probe outputs, accuracy)
    """
    av_probe_outputs = []
    total, correct = 0, 0
    
    for i in range(len(test_df)):
        total += 1
        prompt = test_df.iloc[i]['prompt']
        label = test_df.iloc[i]['label']
        
        avg_probe_output, probe_outputs = evaluate_probe_on_string(
            prompt, model, tokenizer, probe, tqa_dataset, device, tokens_to_average
        )
        
        if verbose and i % (len(test_df) // 10) == 0:
            print(f"Evaluating {i}/{len(test_df)}", end="\t")
            print(f"Probe outputs: {probe_outputs}")
            
        # evaluate
        if label == 1 and avg_probe_output > 0.5:
            correct += 1
        elif label == 0 and avg_probe_output <= 0.5:
            correct += 1
            
        av_probe_outputs.append(avg_probe_output)
        
    accuracy = correct / total
    print(f"Accuracy: {accuracy}")
    return av_probe_outputs, accuracy