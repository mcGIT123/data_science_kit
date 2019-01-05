#!/usr/bin/env python
# -*- coding: utf-8 -*-

import torch
from dtsckit.metrics import AverageKeeper


def train_epoch(epoch, model, dataloader, criterion, optimizer, device, print_rate=50):
    """Train the model for an epoch and return the average training loss

    Parameters
    ----------
    epoch: int
        The number id of this epoch
    model: torch.nn.Module
        The pytorch neural network model
    dataloader: torch.utils.data.DataLoader
        The dataloader that will shuffle and batch the dataset
    criterion: nn.Module/callable
        The loss criterion for the model
    optimizer: pytorch Optimizer
        The optimizer for this model
    device: torch.device
        The device for where the model will be trained
    print_rate: int
        The number of batches to print the status update. If -1 nothing will be printed (default=50)
    """
    print_stats = (print_rate != -1)
    if print_stats:
        print('----------------------')
        print(f'Training epoch {epoch}')
        print('----------------------')
        print('Batch\tAverage Loss')
    loss_avg = AverageKeeper()
    model = model.train()
    for i, batch in enumerate(dataloader):
        images = batch[0].to(device)
        breeds = batch[1].to(device)
        optimizer.zero_grad()
        out = model(images)
        loss = criterion(out, breeds)
        loss.backward()
        optimizer.step()

        loss_avg.add(loss.detach().item())
        if print_stats and i % print_rate == 0:
            print(f'{i}\t{round(loss_avg.calculate(), 6)}')
    return loss_avg.calculate()


def validate_epoch(epoch, model, dataloader, criterion, device, print_rate=50):
    """Validate the model for an epoch and return the average validation loss

    Parameters
    ----------
    epoch: int
        The number id of this epoch
    model: torch.nn.Module
        The pytorch neural network model
    dataloader: torch.utils.data.DataLoader
        The dataloader that will shuffle and batch the dataset
    criterion: nn.Module/callable
        The loss criterion for the model
    device: torch.device
        The device for where the model will be trained
    print_rate: int
        The number of batches to print the status update. If -1 nothing will be printed (default=50)
    """
    print_stats = (print_rate != -1)
    if print_stats:
        print('----------------------')
        print(f'Validation epoch {epoch}')
        print('----------------------')
        print('Batch\tAverage Loss')
    loss_avg = AverageKeeper()
    model = model.eval()
    with torch.no_grad():
        for i, batch in enumerate(dataloader):
            images = batch[0].to(device)
            breeds = batch[1].to(device)
            out = model(images)
            loss = criterion(out, breeds)
            loss_avg.add(loss.detach().item())
            if print_stats and i % print_rate == 0:
                print(f'{i}\t{round(loss_avg.calculate(), 6)}')
    return loss_avg.calculate()


def early_stop(train_loader, eval_loader, model, optimizer, criterion, device,
               print_rate=50, maxepochs=500, check=1, patience=5):

    epoch = 0
    p = 0
    best_validation_loss = float('inf')
    stop_epoch = 0

    training_losses = []
    validation_losses = []

    # while the validation loss has not consistently increased
    while p < patience:

        # train the model for check steps
        for i in range(check):

            if epoch == maxepochs:
                return stop_epoch, training_losses, validation_losses

            training_loss = train_epoch(epoch, model, train_loader, criterion, optimizer, device, print_rate)
            training_losses.append(training_loss)
            epoch += 1

        # get the validation loss
        validation_loss = validate_epoch(epoch, model, eval_loader, criterion, device, print_rate)
        validation_losses.append(validation_loss)

        if validation_loss < best_validation_loss:

            p = 0
            best_validation_loss = validation_loss

            # save the model and update the stopping epoch
            stop_epoch = epoch

        else:
            p += 1

    return stop_epoch, training_losses, validation_losses
